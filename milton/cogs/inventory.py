import logging
from dataclasses import dataclass
from copy import deepcopy
from difflib import SequenceMatcher as match

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from milton.core.bot import Milton

log = logging.getLogger(__name__)

class ItemNotFoundError(Exception):
    """Raised when an item is not found."""

@dataclass
class ItemLocation:
    id: str
    room: str
    location: str

@dataclass
class InventoryItem:
    id: str
    aliases: list[str]
    name: str
    position_id: str
    location: ItemLocation
    quantity: int
    size: str
    description: str


class Inventory(commands.Cog, name="Inventory"):
    """Cog that hosts toy commands."""

    def __init__(self, bot: Milton) -> None:
        self.bot: Milton = bot
    
    async def fetch_all_items(self) -> list[InventoryItem]:
        """Fetch all registered items."""
        log.debug("Fetching all items")
        async with self.bot.db.execute("SELECT DISTINCT id FROM TABLE reagents") as cursor:
            items = self.fetch_items(cursor.fetchall())

        log.debug(f"Found {len(items)} items")

        return items

    async def fetch_items(self, ids: list[str]) -> dict[str, InventoryItem]:
        """Fetch items by their IDs.

        Always returns a list. IDs not in the database are ignored.
        Therefore, can return an empty list if no IDs were found.
        """
        log.debug(f"Fetching {len(ids)} items")
        items = {}
        async with self.bot.db.execute((
            "SELECT id, name, position_id, description, quantity, size "
            "FROM reagents "
            "WHERE id IN :ids"
            ), (ids,)) as cursor:
            async for row in cursor:
                id, name, position_id, desc, quantity, size = row
                items[id] = InventoryItem(
                        id = id, name = name, quantity=quantity, size = size,
                        description=desc, position_id=position_id
                    )
        log.info(f"Found {len(items)} items in 'reagents' table")

        positions = [item.position_id for item in items.values()]
        locations = {}
        async with self.bot.db.execute((
            "SELECT id, room, location FROM positions WHERE id IN :positions"
        ), (positions,)) as cursor:
            async for row in cursor:
                id, room, location = row
                locations[id] = ItemLocation(id=id, room=room, location=location)

        log.info(f"Found {len(locations)} locations")
    
        names = [item.name for item in items.values()]
        aliases = {}
        async with self.bot.db.execute((
            "SELECT primary_name, synonym FROM synonyms WHERE primary_name IN :names",
            ), (names,)) as cursor:
            async for row in cursor:
                name, synonym = row
                if name in aliases:
                    aliases[name].append(synonym)
                else:
                    aliases[name] = [synonym]
        log.info(f"Found {len(aliases)} synonyms")
        
        named_items = []
        for item in items.values():
            named_item = deepcopy(item)
            named_item.aliases = aliases.get(named_item.name, [])
            named_items.append(named_item)
        
        log.info(f"Fetched {len(named_items)} items") 

        return named_items
        

    async def find_items_by_name(self, search_string: str) -> list[InventoryItem]:
        """Fuzzy-find an item by its name or aliases."""
        items = self.fetch_all_items()

        name_distances = [(item, match(item.name, search_string).ratio()) for item in items]
        alias_distances = [(item, [match(alias, search_string).ratio() for alias in item]) for item in items]
        name_distances.extend(alias_distances)
        
        valid_items = [item for (item, ratio) in name_distances if ratio > 0.6]
        valid_items = set(valid_items)
        
        return valid_items

    async def find_items_by_location(self, guild_id: int, search_string: str) -> list[InventoryItem]:
        """Fuzzy-find items by their locations"""
        items = self.fetch_all_items()

        loc_distances = [(item, match(item.location, search_string).ratio()) for item in items]
        room_distances = [(item, match(item.room, search_string).ratio()) for item in items]
        loc_distances.extend(room_distances)
        
        valid_items = [item for (item, ratio) in loc_distances if ratio > 0.6]
        valid_items = set(valid_items)
        
        return valid_items


    async def remove_item(self, id: str) -> None:
        """Remove an item by its ID."""
        async with self.bot.db.execute("SELECT id FROM reagents") as cursor:
            ids = cursor.fetchall()

        if id not in ids:
            raise ItemNotFoundError(f"Couldn't find an item with ID {id}")

        await self.bot.db.execute("DELETE FROM reagents WHERE id = :id", (id, ))
        await self.cleanup_db()

    async def cleanup_db(self) -> None:
        """Cleanup the database of useless locations and aliases

        It may happen that there could be locations or aliases without any
        items that use them. 

        This check for any of these 'useless' entries and gets rid of them.
        """
        # TODO: implement me
        pass


    @app_commands.command()
    @app_commands.guild_only()
    async def add(
        self,
        interaction: Interaction,
    ):
        """Add an item to the inventory."""
        pass

    @app_commands.command()
    @app_commands.guild_only()
    async def remove(self, interaction: Interaction):
        """Remove an item from the inventory.
        """
        pass

    @app_commands.command()
    @app_commands.guild_only()
    async def search(self, interaction: Interaction):
        """Search for an item in the inventory.
        """

    @app_commands.command(name = "setinvmanager")
    @app_commands.checks.has_permissions(administrator = True)
    @app_commands.guild_only()
    async def set_inventory_manager(self, interaction: Interaction, role: discord.Role):
        pass


async def setup(bot: Milton):

    await bot.db.execute((
        'CREATE TABLE IF NOT EXIST "positions" ('
	    '"id"	TEXT NOT NULL UNIQUE,'
	    '"room"	TEXT NOT NULL,'
	    '"location"	TEXT NOT NULL'
        ')'
    ))

    await bot.db.execute((
        'CREATE TABLE "reagents" ('
        '"name"	TEXT NOT NULL UNIQUE,'
        '"id"	TEXT NOT NULL UNIQUE,'
        '"position_id"	TEXT NOT NULL,'
        '"description"	TEXT,'
        '"quantity"	INTEGER,'
        '"size"	TEXT'
        ')'
    ))

    await bot.db.execute((
        'CREATE TABLE "synonyms" ('
    	'"primary_name"	TEXT,'
	    '"synonym"	TEXT'
        ')'
    ))

    await bot.add_cog(Inventory(bot))

