# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from tuxemon.db import ElementType, db
from tuxemon.item.itemeffect import ItemEffect, ItemEffectResult

if TYPE_CHECKING:
    from tuxemon.item.item import Item
    from tuxemon.monster import Monster


class LearnMmEffectResult(ItemEffectResult):
    pass


@dataclass
class LearnMmEffect(ItemEffect):
    """This effect teaches the target a random type technique."""

    name = "learn_mm"
    element: str

    def apply(
        self, item: Item, target: Union[Monster, None]
    ) -> LearnMmEffectResult:
        learn: bool = False
        ele = ElementType(self.element)
        assert target
        techs = list(db.database["technique"])
        # type moves
        filters = []
        for mov in techs:
            results = db.lookup(mov, table="technique")
            if results.randomly:
                if ele in results.types:
                    filters.append(results.slug)
        # monster moves
        moves = []
        for tech in target.moves:
            moves.append(tech.slug)
        # remove monster moves from type moves
        set1 = set(filters)
        set2 = set(moves)
        res = list(set1 - set2)
        # add a random move from what remains
        if res:
            self.user.game_variables["overwrite_technique"] = random.choice(
                res
            )
            learn = True

        return {"success": learn, "num_shakes": 0, "extra": None}
