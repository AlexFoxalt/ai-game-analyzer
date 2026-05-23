from pydantic import BaseModel, Field

from src.kb import HERO_ID_TO_NAME, ITEM_ID_TO_NAME


class ExtraAllowModel(BaseModel):
    model_config = {"extra": "allow"}


class PlayerData(ExtraAllowModel):
    account_id: int | None = Field(None, description="The player account ID. None means account is private")
    hero_id: int = Field(description="The ID value of the hero played")
    item_0: int = Field(description="Item in the player's first slot")
    item_1: int = Field(description="Item in the player's second slot")
    item_2: int = Field(description="Item in the player's third slot")
    item_3: int = Field(description="Item in the player's fourth slot")
    item_4: int = Field(description="Item in the player's fifth slot")
    item_5: int = Field(description="Item in the player's sixth slot")
    backpack_0: int = Field(description="Item in backpack slot 0")
    backpack_1: int = Field(description="Item in backpack slot 1")
    backpack_2: int = Field(description="Item in backpack slot 2")
    item_neutral: int = Field(description="Item in the player's neutral slot")
    item_neutral2: int = Field(description="Item in the player's neutral slot 2")
    kills: int = Field(description="Number of kills")
    deaths: int = Field(description="Total deaths the player had at the end of the game")
    assists: int = Field(description="Total assists the player had at the end of the game")
    leaver_status: int = Field(
        description="Integer describing whether or not the player left the game. 0: didn't leave. 1: left safely. 2+: Abandoned"
    )
    last_hits: int = Field(description="Number of last hits")
    denies: int = Field(description="Number of denies")
    gold_per_min: int = Field(description="Gold Per Minute obtained by this player")
    xp_per_min: int = Field(description="Experience Per Minute obtained by the player")
    level: int = Field(description="Level at the end of the game")
    net_worth: int = Field(description="Total net worth at the end of the game")
    aghanims_scepter: int = Field(description="Binary integer indicating whether the player had Aghanim's Scepter")
    aghanims_shard: int = Field(description="Binary integer indicating whether the player had Aghanim's Shard")
    moonshard: int = Field(description="Binary integer indicating whether the player had Moon Shard")
    hero_damage: int = Field(description="Hero Damage Dealt")
    tower_damage: int = Field(description="Total tower damage done by the player")
    hero_healing: int = Field(description="Hero Healing Done")
    gold: int = Field(description="Gold at the end of the game")
    personaname: str | None = Field(None, description="Player's Steam name. None means account is private")
    start_time: int = Field(description="The Unix timestamp at which the game started")
    duration: int = Field(description="Duration of the game in seconds")
    isRadiant: bool = Field(description="Boolean for whether or not the player is on Radiant")
    win: bool = Field(description="Binary integer representing whether or not the player won")
    lose: bool = Field(description="Binary integer representing whether or not the player lost")
    total_gold: int = Field(description="Total gold at the end of the game")
    total_xp: int = Field(description="Total experience at the end of the game")
    kda: float = Field(description="KDA ratio")
    lh_t: list[int] | None = Field(
        None,
        description="Timeline of cumulative last hits by minute. Useful to evaluate laning efficiency and farm pace in early game.",
    )
    dn_t: list[int] | None = Field(
        None,
        description="Timeline of cumulative denies by minute. Useful to evaluate lane pressure and creep control during lane stage.",
    )
    gold_t: list[int] | None = Field(
        None,
        description="Timeline of total gold by minute. Useful to evaluate laning economy and early net worth progression.",
    )
    xp_t: list[int] | None = Field(
        None,
        description="Timeline of total experience by minute. Useful to evaluate early level timing and lane experience efficiency.",
    )
    lane: int | None = Field(
        None,
        description="Lane assignment identifier for the player in this match (top/mid/bottom encoded by OpenDota constants).",
    )
    lane_role: int | None = Field(
        None,
        description="Lane role identifier (safe/mid/offlane style role encoded by OpenDota constants).",
    )
    is_roaming: bool | None = Field(
        None,
        description="Whether the player was classified as roaming instead of staying in a fixed lane.",
    )
    lane_efficiency_pct: float | None = Field(
        None,
        description="Laning efficiency percentage from OpenDota. Higher values generally indicate stronger lane farm execution.",
    )
    first_purchase_time: dict | None = Field(
        None,
        description="Mapping of item name to first purchase time (seconds). Useful for key timing analysis such as first major power spike.",
    )
    purchase_log: list[dict] | None = Field(
        None,
        description="Chronological log of item purchases with timestamps. Useful to evaluate build order quality and timing windows.",
    )
    purchase_tpscroll: int | None = Field(
        None,
        description="Total number of Town Portal Scrolls purchased. Useful to estimate map reaction discipline and rotation readiness.",
    )
    obs_placed: int | None = Field(
        None,
        description="Total number of observer wards placed by the player. Core signal of vision contribution.",
    )
    sen_placed: int | None = Field(
        None,
        description="Total number of sentry wards placed by the player. Useful to evaluate detection and defensive vision support.",
    )
    observer_kills: int | None = Field(
        None,
        description="Number of enemy observer wards destroyed by the player. Measures deward impact.",
    )
    sentry_kills: int | None = Field(
        None,
        description="Number of enemy sentry wards destroyed by the player. Measures deward and map control impact.",
    )
    obs_log: list[dict] | None = Field(
        None,
        description="Chronological log of observer ward placements with time and map location details.",
    )
    sen_log: list[dict] | None = Field(
        None,
        description="Chronological log of sentry ward placements with time and map location details.",
    )
    obs_left_log: list[dict] | None = Field(
        None,
        description="Observer ward duration/expiration related log from OpenDota. Useful for ward uptime context.",
    )
    sen_left_log: list[dict] | None = Field(
        None,
        description="Sentry ward duration/expiration related log from OpenDota. Useful for detection uptime context.",
    )
    teamfights: list[dict] | None = Field(
        None,
        description="Detailed teamfight event data involving this player (when available). Useful to evaluate fight participation and impact windows.",
    )
    stuns: float | None = Field(
        None,
        description="Total stun duration applied by the player. Useful to evaluate disable impact in skirmishes and full teamfights.",
    )
    damage_inflictor: dict | None = Field(
        None,
        description="Breakdown of hero damage by source (spells/attacks/items). Useful to evaluate whether damage profile matches hero role.",
    )
    damage_taken: dict | None = Field(
        None,
        description="Breakdown of incoming damage sources. Useful to analyze survivability issues and positioning risks.",
    )
    buyback_count: int | None = Field(
        None,
        description="Total number of buybacks used by the player. Useful to analyze high-pressure decisions and late-game discipline.",
    )
    buyback_log: list[dict] | None = Field(
        None,
        description="Chronological log of buyback events with timestamps. Useful for evaluating buyback timing quality around objectives and base defense.",
    )
    tower_kills: int | None = Field(
        None,
        description="Total number of towers last-hit by the player. Proxy for objective finishing contribution.",
    )
    roshan_kills: int | None = Field(
        None,
        description="Total number of Roshan last hits by the player. Proxy for Aegis-control contribution.",
    )
    runes: dict | None = Field(
        None,
        description="Breakdown of rune types picked by the player. Useful for activity and power-rune control context.",
    )
    rune_pickups: int | None = Field(
        None,
        description="Total number of runes picked up by the player. Useful for map activity and bottle/rune control context.",
    )
    camps_stacked: int | None = Field(
        None,
        description="Number of neutral camps stacked by the player. Proxy for support utility and farm-acceleration contribution.",
    )


class NormalizedPlayerData(ExtraAllowModel):
    account_id: int | None = Field(None, description="The player account ID. None means account is private")

    # Mapped ID to name
    hero_name: str = Field(description="The name of the hero played")
    item_0: str = Field(description="The name of the item in the player's first slot")
    item_1: str = Field(description="The name of the item in the player's second slot")
    item_2: str = Field(description="The name of the item in the player's third slot")
    item_3: str = Field(description="The name of the item in the player's fourth slot")
    item_4: str = Field(description="The name of the item in the player's fifth slot")
    item_5: str = Field(description="The name of the item in the player's sixth slot")
    backpack_0: str = Field(description="The name of the item in backpack slot 0")
    backpack_1: str = Field(description="The name of the item in backpack slot 1")
    backpack_2: str = Field(description="The name of the item in backpack slot 2")
    item_neutral: str = Field(description="The name of the item in the player's neutral slot")
    item_neutral2: str = Field(description="The name of the item in the player's neutral slot 2")

    kills: int = Field(description="Number of kills")
    deaths: int = Field(description="Total deaths the player had at the end of the game")
    assists: int = Field(description="Total assists the player had at the end of the game")
    leaver_status: int = Field(
        description="Integer describing whether or not the player left the game. 0: didn't leave. 1: left safely. 2+: Abandoned"
    )
    last_hits: int = Field(description="Number of last hits")
    denies: int = Field(description="Number of denies")
    gold_per_min: int = Field(description="Gold Per Minute obtained by this player")
    xp_per_min: int = Field(description="Experience Per Minute obtained by the player")
    level: int = Field(description="Level at the end of the game")
    net_worth: int = Field(description="Total net worth at the end of the game")
    aghanims_scepter: int = Field(description="Binary integer indicating whether the player had Aghanim's Scepter")
    aghanims_shard: int = Field(description="Binary integer indicating whether the player had Aghanim's Shard")
    moonshard: int = Field(description="Binary integer indicating whether the player had Moon Shard")
    hero_damage: int = Field(description="Hero Damage Dealt")
    tower_damage: int = Field(description="Total tower damage done by the player")
    hero_healing: int = Field(description="Hero Healing Done")
    gold: int = Field(description="Gold at the end of the game")
    personaname: str | None = Field(None, description="Player's Steam name. None means account is private")
    start_time: int = Field(description="The Unix timestamp at which the game started")
    duration: int = Field(description="Duration of the game in seconds")
    isRadiant: bool = Field(description="Boolean for whether or not the player is on Radiant")
    win: bool = Field(description="Binary integer representing whether or not the player won")
    lose: bool = Field(description="Binary integer representing whether or not the player lost")
    total_gold: int = Field(description="Total gold at the end of the game")
    total_xp: int = Field(description="Total experience at the end of the game")
    kda: float = Field(description="KDA ratio")
    lh_t: list[int] | None = Field(
        None,
        description="Timeline of cumulative last hits by minute. Useful to evaluate laning efficiency and farm pace in early game.",
    )
    dn_t: list[int] | None = Field(
        None,
        description="Timeline of cumulative denies by minute. Useful to evaluate lane pressure and creep control during lane stage.",
    )
    gold_t: list[int] | None = Field(
        None,
        description="Timeline of total gold by minute. Useful to evaluate laning economy and early net worth progression.",
    )
    xp_t: list[int] | None = Field(
        None,
        description="Timeline of total experience by minute. Useful to evaluate early level timing and lane experience efficiency.",
    )
    lane: int | None = Field(
        None,
        description="Lane assignment identifier for the player in this match (top/mid/bottom encoded by OpenDota constants).",
    )
    lane_role: int | None = Field(
        None,
        description="Lane role identifier (safe/mid/offlane style role encoded by OpenDota constants).",
    )
    is_roaming: bool | None = Field(
        None,
        description="Whether the player was classified as roaming instead of staying in a fixed lane.",
    )
    lane_efficiency_pct: float | None = Field(
        None,
        description="Laning efficiency percentage from OpenDota. Higher values generally indicate stronger lane farm execution.",
    )
    first_purchase_time: dict | None = Field(
        None,
        description="Mapping of item name to first purchase time (seconds). Useful for key timing analysis such as first major power spike.",
    )
    purchase_log: list[dict] | None = Field(
        None,
        description="Chronological log of item purchases with timestamps. Useful to evaluate build order quality and timing windows.",
    )
    purchase_tpscroll: int | None = Field(
        None,
        description="Total number of Town Portal Scrolls purchased. Useful to estimate map reaction discipline and rotation readiness.",
    )
    obs_placed: int | None = Field(
        None,
        description="Total number of observer wards placed by the player. Core signal of vision contribution.",
    )
    sen_placed: int | None = Field(
        None,
        description="Total number of sentry wards placed by the player. Useful to evaluate detection and defensive vision support.",
    )
    observer_kills: int | None = Field(
        None,
        description="Number of enemy observer wards destroyed by the player. Measures deward impact.",
    )
    sentry_kills: int | None = Field(
        None,
        description="Number of enemy sentry wards destroyed by the player. Measures deward and map control impact.",
    )
    obs_log: list[dict] | None = Field(
        None,
        description="Chronological log of observer ward placements with time and map location details.",
    )
    sen_log: list[dict] | None = Field(
        None,
        description="Chronological log of sentry ward placements with time and map location details.",
    )
    obs_left_log: list[dict] | None = Field(
        None,
        description="Observer ward duration/expiration related log from OpenDota. Useful for ward uptime context.",
    )
    sen_left_log: list[dict] | None = Field(
        None,
        description="Sentry ward duration/expiration related log from OpenDota. Useful for detection uptime context.",
    )
    teamfights: list[dict] | None = Field(
        None,
        description="Detailed teamfight event data involving this player (when available). Useful to evaluate fight participation and impact windows.",
    )
    stuns: float | None = Field(
        None,
        description="Total stun duration applied by the player. Useful to evaluate disable impact in skirmishes and full teamfights.",
    )
    damage_inflictor: dict | None = Field(
        None,
        description="Breakdown of hero damage by source (spells/attacks/items). Useful to evaluate whether damage profile matches hero role.",
    )
    damage_taken: dict | None = Field(
        None,
        description="Breakdown of incoming damage sources. Useful to analyze survivability issues and positioning risks.",
    )
    buyback_count: int | None = Field(
        None,
        description="Total number of buybacks used by the player. Useful to analyze high-pressure decisions and late-game discipline.",
    )
    buyback_log: list[dict] | None = Field(
        None,
        description="Chronological log of buyback events with timestamps. Useful for evaluating buyback timing quality around objectives and base defense.",
    )
    tower_kills: int | None = Field(
        None,
        description="Total number of towers last-hit by the player. Proxy for objective finishing contribution.",
    )
    roshan_kills: int | None = Field(
        None,
        description="Total number of Roshan last hits by the player. Proxy for Aegis-control contribution.",
    )
    runes: dict | None = Field(
        None,
        description="Breakdown of rune types picked by the player. Useful for activity and power-rune control context.",
    )
    rune_pickups: int | None = Field(
        None,
        description="Total number of runes picked up by the player. Useful for map activity and bottle/rune control context.",
    )
    camps_stacked: int | None = Field(
        None,
        description="Number of neutral camps stacked by the player. Proxy for support utility and farm-acceleration contribution.",
    )

    @staticmethod
    def from_player_data(player_data: PlayerData) -> "NormalizedPlayerData":
        _def = "Unknown"
        return NormalizedPlayerData(
            account_id=player_data.account_id,
            hero_name=HERO_ID_TO_NAME.get(str(player_data.hero_id), _def),
            item_0=ITEM_ID_TO_NAME.get(str(player_data.item_0), _def),
            item_1=ITEM_ID_TO_NAME.get(str(player_data.item_1), _def),
            item_2=ITEM_ID_TO_NAME.get(str(player_data.item_2), _def),
            item_3=ITEM_ID_TO_NAME.get(str(player_data.item_3), _def),
            item_4=ITEM_ID_TO_NAME.get(str(player_data.item_4), _def),
            item_5=ITEM_ID_TO_NAME.get(str(player_data.item_5), _def),
            backpack_0=ITEM_ID_TO_NAME.get(str(player_data.backpack_0), _def),
            backpack_1=ITEM_ID_TO_NAME.get(str(player_data.backpack_1), _def),
            backpack_2=ITEM_ID_TO_NAME.get(str(player_data.backpack_2), _def),
            item_neutral=ITEM_ID_TO_NAME.get(str(player_data.item_neutral), _def),
            item_neutral2=ITEM_ID_TO_NAME.get(str(player_data.item_neutral2), _def),
            kills=player_data.kills,
            deaths=player_data.deaths,
            assists=player_data.assists,
            leaver_status=player_data.leaver_status,
            last_hits=player_data.last_hits,
            denies=player_data.denies,
            gold_per_min=player_data.gold_per_min,
            xp_per_min=player_data.xp_per_min,
            level=player_data.level,
            net_worth=player_data.net_worth,
            aghanims_scepter=player_data.aghanims_scepter,
            aghanims_shard=player_data.aghanims_shard,
            moonshard=player_data.moonshard,
            hero_damage=player_data.hero_damage,
            tower_damage=player_data.tower_damage,
            hero_healing=player_data.hero_healing,
            gold=player_data.gold,
            personaname=player_data.personaname,
            start_time=player_data.start_time,
            duration=player_data.duration,
            isRadiant=player_data.isRadiant,
            win=player_data.win,
            lose=player_data.lose,
            total_gold=player_data.total_gold,
            total_xp=player_data.total_xp,
            kda=player_data.kda,
            lh_t=player_data.lh_t,
            dn_t=player_data.dn_t,
            gold_t=player_data.gold_t,
            xp_t=player_data.xp_t,
            lane=player_data.lane,
            lane_role=player_data.lane_role,
            is_roaming=player_data.is_roaming,
            lane_efficiency_pct=player_data.lane_efficiency_pct,
            first_purchase_time=player_data.first_purchase_time,
            purchase_log=player_data.purchase_log,
            purchase_tpscroll=player_data.purchase_tpscroll,
            obs_placed=player_data.obs_placed,
            sen_placed=player_data.sen_placed,
            observer_kills=player_data.observer_kills,
            sentry_kills=player_data.sentry_kills,
            obs_log=player_data.obs_log,
            sen_log=player_data.sen_log,
            obs_left_log=player_data.obs_left_log,
            sen_left_log=player_data.sen_left_log,
            teamfights=player_data.teamfights,
            stuns=player_data.stuns,
            damage_inflictor=player_data.damage_inflictor,
            damage_taken=player_data.damage_taken,
            buyback_count=player_data.buyback_count,
            buyback_log=player_data.buyback_log,
            tower_kills=player_data.tower_kills,
            roshan_kills=player_data.roshan_kills,
            runes=player_data.runes,
            rune_pickups=player_data.rune_pickups,
            camps_stacked=player_data.camps_stacked,
        )


class Match(ExtraAllowModel):
    model_config = {"extra": "ignore"}

    match_id: int = Field(description="The ID number of the match assigned by Valve")
    radiant_win: bool = Field(description="Boolean indicating whether Radiant won the match")
    start_time: int = Field(description="The Unix timestamp at which the game started")
    duration: int = Field(description="Duration of the game in seconds")
    party_size: int | None = Field(None, description="Size of the player's party")
    overview: dict[str, str] | str | None = Field(
        None,
        description="Compact LLM-generated player overviews for historical context (player_id -> plain text)",
    )

    data: list[PlayerData] | None = Field(None, description="List of players data in the match")
