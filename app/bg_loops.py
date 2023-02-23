from __future__ import annotations

import asyncio
import time
from typing import Union

from circleguard import Circleguard
from circleguard import ReplayString
from discord_webhook import DiscordEmbed
from discord_webhook import DiscordWebhook

import app.packets
import app.settings
import app.state
from app.constants.gamemodes import GameMode
from app.constants.mods import Mods
from app.constants.privileges import Privileges
from app.discord import Embed
from app.discord import Webhook
from app.logging import Ansi
from app.logging import log
from app.objects.score import Score

__all__ = ("initialize_housekeeping_tasks",)

OSU_CLIENT_MIN_PING_INTERVAL = 300000 // 1000  # defined by osu!


def _get_conversion_factor(score_mods: Mods) -> Union[float, int]:
    if Mods.DOUBLETIME & score_mods:
        return 1 / 1.5
    if Mods.HALFTIME in score_mods:
        return 1 / 0.75

    return 1


async def initialize_housekeeping_tasks() -> None:
    """Create tasks for each housekeeping tasks."""
    log("Initializing housekeeping tasks.", Ansi.LCYAN)

    loop = asyncio.get_running_loop()

    app.state.sessions.housekeeping_tasks.update(
        {
            loop.create_task(task)
            for task in (
                _remove_expired_donation_privileges(interval=30 * 60),
                _update_bot_status(interval=5 * 60),
                _disconnect_ghosts(interval=OSU_CLIENT_MIN_PING_INTERVAL // 3),
                _rankrecalc(interval=1440 * 60),
                _replay_detections(),
                _handle_scores(),
            )
        },
    )


async def _handle_scores() -> None:
    """Handle score queue to process sensetive data."""
    while score := await app.state.sessions.score_queue.get():
        app.state.loop.create_task(score.handle_sensetive_data())


async def _remove_expired_donation_privileges(interval: int) -> None:
    """Remove donation privileges from users with expired sessions."""
    while True:
        if app.settings.DEBUG:
            log("Removing expired donation privileges.", Ansi.LMAGENTA)

        expired_donors = await app.state.services.database.fetch_all(
            "SELECT id FROM users "
            "WHERE donor_end <= UNIX_TIMESTAMP() "
            "AND priv & 48",  # 48 = Supporter | Premium
        )

        for expired_donor in expired_donors:
            p = await app.state.sessions.players.from_cache_or_sql(
                id=expired_donor["id"],
            )

            assert p is not None

            # TODO: perhaps make a `revoke_donor` method?
            await p.remove_privs(Privileges.DONATOR)
            p.donor_end = 0
            await app.state.services.database.execute(
                "UPDATE users SET donor_end = 0 WHERE id = :id",
                {"id": p.id},
            )

            if p.online:
                p.enqueue(
                    app.packets.notification("Your supporter status has expired."),
                )

            log(f"{p}'s supporter status has expired.", Ansi.LMAGENTA)

        await asyncio.sleep(interval)


PUBLIC_PATH = app.settings.GULAG_WEB_PATH / "static/framegraphs"
# This function is currently pretty tiny and useless, but
# will just continue to expand as more ideas come to mind.
async def _analyze_score(score: "Score") -> None:
    """Analyze a single score."""
    # NOTE: Need to figure out way to detect relax mod hackers
    # Progression: Find way to get amount of frames on excepted frametime
    if score.mode.value not in (0, 4, 8) or score.player.restricted:
        return

    # Wait for replay?
    await asyncio.sleep(0.5)

    player = score.player
    circle_guard = Circleguard(app.settings.OSU_API_KEY)

    # Base Webhook
    webhook = Webhook(url=app.settings.DISCORD_AUDIT_LOG_WEBHOOK)

    # get & parse replay files frames
    replay_file = await app.state.services.http.get(
        f"https://api.{app.settings.DOMAIN}/get_replay?id={score.id}",
        verify_ssl=False,
    )
    replay = ReplayString(await replay_file.read())

    # UR Check
    if (replay_ur := circle_guard.ur(replay)) < app.settings.UNSTABLE_RATE_CAP:
        embed = Embed(
            title=f"[{score.mode!r}] Possibly relax score. ({replay_ur} UR)",
            color=0xBB0EBE,
        )

        embed.set_author(url=player.url, name=player.name, icon_url=player.avatar_url)

        embed.set_thumbnail(url=f"https://osu.okayu.me/static/favicon/favicon.ico")

        embed.add_field(
            name="Map",
            value=f"[{score.bmap.full_name}](https://osu.{app.settings.DOMAIN}/b/{score.bmap.id})",
        )

        embed.add_field(
            name="Replay",
            value=f"[Download](https://api.{app.settings.DOMAIN}/get_replay?id={score.id})",
        )

        webhook.add_embed(embed)

    # Frametime check
    frametime = circle_guard.frametime(replay)
    if score.mode != GameMode.RELAX_OSU:
        if frametime <= app.settings.FRAME_TIME_CAP:
            embed = Embed(
                title=f"[{score.mode!r}] Possibly Timewarped score. ({frametime} avg. frametime)",
                color=0xBB0EBE,
            )

            embed.set_author(
                url=player.url,
                name=player.name,
                icon_url=player.avatar_url,
            )

            embed.set_thumbnail(
                url=f"https://osu.{app.settings.DOMAIN}/static/ingame.png",
            )

            embed.add_field(
                name="Map",
                value=f"[{score.bmap.full_name}](https://osu.{app.settings.DOMAIN}/b/{score.bmap.id})",
            )

            embed.add_field(
                name="Replay",
                value=f"[Download](https://api.{app.settings.DOMAIN}/get_replay?id={score.id})",
            )
    else:
        frametimes = circle_guard.frametimes(replay, cv=False)
        excepted_frametime = 16 + 2 / 3

        frametimes = _get_conversion_factor(score.mods) * frametimes

        frames_before = sum(i < excepted_frametime for i in frametimes)
        frames_after = sum(i >= excepted_frametime for i in frametimes)

        if (frames_after / frames_before) * 100 <= app.settings.RX_FRAME_TIME_MP:
            embed = Embed(
                title=f"[{score.mode!r}] Possibly Timewarped score. ({frametime} avg. frametime)",
                color=0xBB0EBE,
            )

            embed.set_author(
                url=player.url,
                name=player.name,
                icon_url=player.avatar_url,
            )

            embed.set_thumbnail(
                url=f"https://osu.{app.settings.DOMAIN}/static/ingame.png",
            )

            embed.add_field(
                name="Map",
                value=f"[{score.bmap.full_name}](https://osu.{app.settings.DOMAIN}/b/{score.bmap.id})",
            )

            embed.add_field(
                name="Replay",
                value=f"[Download](https://api.{app.settings.DOMAIN}/get_replay?id={score.id})",
            )

            graph_obj = circle_guard.frametime_graph(replay)
            graph_obj.savefig(PUBLIC_PATH / f"{score.id}_ft.png")

            embed.set_image(
                url=f"https://osu.{app.settings.DOMAIN}/static/framegraphs/{score.id}_ft.png",
            )

            webhook.add_embed(embed)

    # Snaps check
    snaps = circle_guard.snaps(replay)
    if len(snaps) > app.settings.SNAPS_CAP:
        embed = Embed(
            title=f"[{score.mode!r}] Too many snaps! ({len(snaps)} snaps)",
            color=0xBB0EBE,
        )

        embed.set_author(url=player.url, name=player.name, icon_url=player.avatar_url)

        embed.set_thumbnail(url=f"https://osu.{app.settings.DOMAIN}/static/ingame.png")

        embed.add_field(
            name="Map",
            value=f"[{score.bmap.full_name}](https://osu.{app.settings.DOMAIN}/b/{score.bmap.id})",
        )

        embed.add_field(
            name="Replay",
            value=f"[Download](https://api.{app.settings.DOMAIN}/get_replay?id={score.id})",
        )

        webhook.add_embed(embed)

    # TODO: Presstime check
    if len(webhook.embeds) > 0:
        await webhook.post(app.state.services.http)


async def _replay_detections() -> None:
    """Actively run a background thread throughout gulag's
    lifespan; it will pull replays determined as sketch
    from a queue indefinitely."""
    while score := await app.state.sessions.queue.get():
        app.state.loop.create_task(_analyze_score(score))


async def _disconnect_ghosts(interval: int) -> None:
    """Actively disconnect users above the
    disconnection time threshold on the osu! server."""
    while True:
        await asyncio.sleep(interval)
        current_time = time.time()

        for p in app.state.sessions.players:
            if current_time - p.last_recv_time > OSU_CLIENT_MIN_PING_INTERVAL:
                log(f"Auto-dced {p}.", Ansi.LMAGENTA)
                p.logout()


async def _update_bot_status(interval: int) -> None:
    """Reroll the bot's status, every `interval`."""
    while True:
        await asyncio.sleep(interval)
        app.packets.bot_stats.cache_clear()


async def _rankrecalc(interval: int) -> None:
    """Update users rank every `interval`."""
    while True:
        await asyncio.sleep(interval)

        scores = await app.state.services.database.fetch_all(
            "SELECT stats.id,users.priv,country,stats.pp,stats.mode FROM `users` INNER JOIN stats on users.id = stats.id",
        )

        staff_chan = app.state.sessions.channels["#staff"]  # log any errs here
        staff_chan.send_bot(f"Auto rank recalculation started.")

        for i in scores:

            if i[1] & Privileges.NORMAL:
                user_id = i[0]
                await app.state.services.redis.zadd(
                    f"bancho:leaderboard:{i[4]}",
                    {str(user_id): i[3]},
                )

                # country rank
                await app.state.services.redis.zadd(
                    f"bancho:leaderboard:{i[4]}:{i[2]}",
                    {str(user_id): i[3]},
                )
