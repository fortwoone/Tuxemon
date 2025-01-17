# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2023 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import math
from functools import partial
from typing import Any, Callable, List

import pygame_menu
from pygame_menu import locals
from pygame_menu.locals import POSITION_CENTER
from pygame_menu.widgets.selection.highlight import HighlightSelection

from tuxemon import formula, prepare, tools
from tuxemon.db import MonsterModel, SeenStatus, db
from tuxemon.locale import T
from tuxemon.menu.menu import BACKGROUND_COLOR, PygameMenuState
from tuxemon.menu.theme import get_theme
from tuxemon.monster import Monster
from tuxemon.session import local_session

MAX_PAGE = 20


MenuGameObj = Callable[[], object]


def fix_width(screen_x: int, pos_x: float) -> int:
    """it returns the correct width based on percentage"""
    value = round(screen_x * pos_x)
    return value


def fix_height(screen_y: int, pos_y: float) -> int:
    """it returns the correct height based on percentage"""
    value = round(screen_y * pos_y)
    return value


class JournalChoice(PygameMenuState):
    """Shows the pages."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monsters: List[MonsterModel],
    ) -> None:
        width = menu._width
        height = menu._height

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        total_monster = len(monsters)
        # defines number of pages based on the total nr of monsters
        # it uses math.ceil because if the diff is < .5 , it must
        # round up (eg. 11.49 > 12)
        diff = math.ceil(total_monster / MAX_PAGE)
        menu._column_max_width = [
            fix_width(width, 0.40),
            fix_width(width, 0.40),
        ]

        for page in range(diff):
            maximum = (page * MAX_PAGE) + MAX_PAGE
            minimum = page * MAX_PAGE
            label = T.format(
                "page_tuxepedia", {"a": str(minimum), "b": str(maximum)}
            ).upper()
            menu.add.button(
                label,
                change_state(
                    "JournalState", kwargs={"monsters": monsters, "page": page}
                ),
                font_size=20,
            ).translate(fix_width(width, 0.18), fix_height(height, 0.01))

    def __init__(self) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/tux_generic.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_LEFT

        columns = 2

        monsters = list(db.database["monster"])
        box = []
        for mov in monsters:
            results = db.lookup(mov, table="monster")
            if results.txmn_id > 0:
                box.append(results)

        diff = round(len(box) / MAX_PAGE) + 1
        rows = int(diff / columns) + 1

        super().__init__(
            height=height, width=width, columns=columns, rows=rows
        )

        menu_items_map = []
        menu_items_map = box

        self.add_menu_items(self.menu, menu_items_map)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT


class JournalState(PygameMenuState):
    """Shows monsters in a single page."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monsters: List[MonsterModel],
    ) -> None:
        width = menu._width
        height = menu._height
        menu._column_max_width = [
            fix_width(width, 0.35),
            fix_width(width, 0.35),
        ]

        def change_state(state: str, **kwargs: Any) -> MenuGameObj:
            return partial(self.client.push_state, state, **kwargs)

        monsters = sorted(monsters, key=lambda x: x.txmn_id)

        player = local_session.player
        for mon in monsters:
            if mon.slug in player.tuxepedia:
                label = str(mon.txmn_id) + ". " + T.translate(mon.slug).upper()
                if player.tuxepedia[mon.slug] == SeenStatus.seen:
                    menu.add.button(
                        label,
                        change_state(
                            "JournalInfoState", kwargs={"monster": mon}
                        ),
                        font_size=20,
                        font_color=(25, 25, 112, 1),
                        selection_color=(25, 25, 112, 1),
                        button_id=mon.slug,
                    ).translate(
                        fix_width(width, 0.25), fix_height(height, 0.01)
                    )
                elif player.tuxepedia[mon.slug] == SeenStatus.caught:
                    menu.add.button(
                        label,
                        change_state(
                            "JournalInfoState", kwargs={"monster": mon}
                        ),
                        font_size=20,
                        button_id=mon.slug,
                        underline=True,
                    ).translate(
                        fix_width(width, 0.25), fix_height(height, 0.01)
                    )
            else:
                label = str(mon.txmn_id) + ". " + T.translate(mon.slug).upper()
                lab = menu.add.label(
                    label,
                    font_size=20,
                    font_color=(105, 105, 105),
                    label_id=mon.slug,
                )
                assert not isinstance(lab, List)
                lab.translate(fix_width(width, 0.25), fix_height(height, 0.01))

    def __init__(self, **kwargs: Any) -> None:
        monsters = ""
        page = 0
        for ele in kwargs.values():
            monsters = ele["monsters"]
            page = ele["page"]

        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/tux_generic.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_LEFT

        columns = 2

        # defines range txmn_ids
        min_txmn = 0
        max_txmn = 0
        if page == 0:
            min_txmn = 0
            max_txmn = MAX_PAGE
        else:
            min_txmn = page * MAX_PAGE
            max_txmn = (page + 1) * MAX_PAGE

        # applies range to tuxemon
        monster_list = []
        for ele in monsters:
            if min_txmn < ele.txmn_id <= max_txmn:
                monster_list.append(ele)

        # fix columns and rows
        num_mon = 0
        if len(monster_list) != MAX_PAGE:
            num_mon = len(monster_list) + 1
        else:
            num_mon = len(monster_list)
        rows = num_mon / columns

        super().__init__(
            height=height, width=width, columns=columns, rows=int(rows)
        )

        self.add_menu_items(self.menu, monster_list)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT


class JournalInfoState(PygameMenuState):
    """Shows details of the single monster."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monster: Monster,
    ) -> None:
        width = menu._width
        height = menu._height
        menu._width = fix_height(menu._width, 0.97)

        name = T.translate(monster.slug).upper()
        desc = T.translate(f"{monster.slug}_description")
        # evolution
        evo = ""
        if monster.evolutions:
            if len(monster.evolutions) == 1:
                evo = T.translate("yes_evolution")
            else:
                evo = T.translate("yes_evolutions")
        else:
            evo = T.translate("no_evolution")
        # types
        types = " ".join(map(lambda s: T.translate(s.name), monster.types))
        # weight and height
        unit = local_session.player.game_variables["unit_measure"]
        if unit == "Metric":
            mon_weight = monster.weight
            mon_height = monster.height
            unit_weight = "kg"
            unit_height = "cm"
        else:
            mon_weight = formula.convert_lbs(monster.weight)
            mon_height = formula.convert_ft(monster.height)
            unit_weight = "lb"
            unit_height = "ft"
        # name
        menu._auto_centering = False
        lab1 = menu.add.label(
            title=name,
            label_id="name",
            font_size=30,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab1, List)
        lab1.translate(fix_width(width, 0.50), fix_height(height, 0.15))
        # weight
        lab2 = menu.add.label(
            title=str(mon_weight) + " " + unit_weight,
            label_id="weight",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab2, List)
        lab2.translate(fix_width(width, 0.50), fix_height(height, 0.25))
        # height
        lab3 = menu.add.label(
            title=str(mon_height) + " " + unit_height,
            label_id="height",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab3, List)
        lab3.translate(fix_width(width, 0.65), fix_height(height, 0.25))
        # type
        lab4 = menu.add.label(
            title=T.translate("monster_menu_type"),
            label_id="type_label",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab4, List)
        lab4.translate(fix_width(width, 0.50), fix_height(height, 0.30))
        type_image_1 = pygame_menu.BaseImage(
            tools.transform_resource_filename(
                f"gfx/ui/icons/element/{monster.types[0].name}_type.png"
            ),
        )
        if len(monster.types) > 1:
            type_image_2 = pygame_menu.BaseImage(
                tools.transform_resource_filename(
                    f"gfx/ui/icons/element/{monster.types[1].name}_type.png"
                ),
            )
            menu.add.image(type_image_1, float=True).translate(
                fix_width(width, 0.17), fix_height(height, 0.29)
            )
            menu.add.image(type_image_2, float=True).translate(
                fix_width(width, 0.19), fix_height(height, 0.29)
            )
        else:
            menu.add.image(type_image_1, float=True).translate(
                fix_width(width, 0.17), fix_height(height, 0.29)
            )
        lab5 = menu.add.label(
            title=types,
            label_id="type_loaded",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab5, List)
        lab5.translate(fix_width(width, 0.50), fix_height(height, 0.35))
        # shape
        shape = (
            T.translate("monster_menu_shape")
            + ": "
            + T.translate(monster.shape)
        )
        lab6 = menu.add.label(
            title=shape,
            label_id="shape",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab6, List)
        lab6.translate(fix_width(width, 0.50), fix_height(height, 0.40))
        # species
        spec = T.translate(f"cat_{monster.category}")
        if monster.category:
            spec = T.translate(monster.category)
        species = T.translate("monster_menu_species") + ": " + spec
        lab7 = menu.add.label(
            title=species,
            label_id="species",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab7, List)
        lab7.translate(fix_width(width, 0.50), fix_height(height, 0.45))
        # txmn_id
        lab8 = menu.add.label(
            title="ID: " + str(monster.txmn_id),
            label_id="txmn_id",
            font_size=18,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab8, List)
        lab8.translate(fix_width(width, 0.50), fix_height(height, 0.10))
        # description
        lab9 = menu.add.label(
            title=desc,
            label_id="description",
            font_size=18,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab9, List)
        lab9.translate(fix_width(width, 0.01), fix_height(height, 0.56))
        # evolution
        lab10 = menu.add.label(
            title=evo,
            label_id="evolution",
            font_size=18,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab10, List)
        lab10.translate(fix_width(width, 0.01), fix_height(height, 0.76))

        # open evolution monster
        def change_state(state: str, monster_slug: str) -> MenuGameObj:
            element = db.lookup(monster_slug, table="monster")
            return partial(
                self.client.push_state, state, kwargs={"monster": element}
            )

        # evolution monsters buttons
        f = menu.add.frame_h(
            float=True,
            width=fix_width(width, 0.95),
            height=fix_width(width, 0.05),
            frame_id="evolutions",
        )
        f.translate(fix_width(width, 0.02), fix_height(height, 0.80))
        f._relax = True
        # removes duplicates
        player = local_session.player
        elements = []
        for ele in monster.evolutions:
            if ele.monster_slug in player.tuxepedia:
                elements.append(ele.monster_slug)
        no_duplicates = sorted(set(elements))
        labels = [
            menu.add.button(
                title=f"{T.translate(ele).upper()}",
                action=change_state("JournalInfoState", ele),
                align=locals.ALIGN_LEFT,
                font_size=15,
                selection_effect=HighlightSelection(),
            )
            for ele in no_duplicates
        ]
        for no_duplicates in labels:
            f.pack(no_duplicates)
        # image
        new_image = pygame_menu.BaseImage(
            tools.transform_resource_filename(
                f"gfx/sprites/battle/{monster.slug}-front.png"
            ),
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_width(width, 0.20), fix_height(height, 0.05)
        )

    def __init__(self, **kwargs: Any) -> None:
        monster = Monster()
        for ele in kwargs.values():
            monster = ele["monster"]

        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/tux_info.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu, monster)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT


class MonsterInfoState(PygameMenuState):
    """Shows details of the single monster."""

    def add_menu_items(
        self,
        menu: pygame_menu.Menu,
        monster: Monster,
    ) -> None:
        width = menu._width
        height = menu._height
        menu._width = fix_height(menu._width, 0.97)
        # evolution
        evo = ""
        if monster.evolutions:
            if len(monster.evolutions) == 1:
                evo = T.translate("yes_evolution")
            else:
                evo = T.translate("yes_evolutions")
        else:
            evo = T.translate("no_evolution")
        # types
        types = " ".join(map(lambda s: T.translate(s.slug), monster.types))
        # weight and height
        results = db.lookup(monster.slug, table="monster")
        diff_weight, diff_height = formula.weight_height_diff(monster, results)
        unit = local_session.player.game_variables["unit_measure"]
        if unit == "Metric":
            mon_weight = monster.weight
            mon_height = monster.height
            unit_weight = "kg"
            unit_height = "cm"
        else:
            mon_weight = formula.convert_lbs(monster.weight)
            mon_height = formula.convert_ft(monster.height)
            unit_weight = "lb"
            unit_height = "ft"
        # name
        menu._auto_centering = False
        lab1 = menu.add.label(
            title=str(monster.txmn_id) + ". " + monster.name.upper(),
            label_id="name",
            font_size=20,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab1, List)
        lab1.translate(fix_width(width, 0.50), fix_height(height, 0.10))
        # level + exp
        exp = monster.total_experience
        lab2 = menu.add.label(
            title="Lv. " + str(monster.level) + " - " + str(exp) + "px",
            label_id="level",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab2, List)
        lab2.translate(fix_width(width, 0.50), fix_height(height, 0.15))
        # exp next level
        exp_lv = monster.experience_required(1) - monster.total_experience
        lv = monster.level + 1
        lab3 = menu.add.label(
            title=T.format("tuxepedia_exp", {"exp_lv": exp_lv, "lv": lv}),
            label_id="exp",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab3, List)
        lab3.translate(fix_width(width, 0.50), fix_height(height, 0.20))
        # weight
        lab4 = menu.add.label(
            title=str(mon_weight)
            + " "
            + unit_weight
            + " ("
            + str(diff_weight)
            + "%)",
            label_id="weight",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab4, List)
        lab4.translate(fix_width(width, 0.50), fix_height(height, 0.25))
        # height
        lab5 = menu.add.label(
            title=str(mon_height)
            + " "
            + unit_height
            + " ("
            + str(diff_height)
            + "%)",
            label_id="height",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab5, List)
        lab5.translate(fix_width(width, 0.50), fix_height(height, 0.30))
        # type
        lab6 = menu.add.label(
            title=types,
            label_id="type",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab6, List)
        lab6.translate(fix_width(width, 0.50), fix_height(height, 0.35))
        # shape
        lab7 = menu.add.label(
            title=T.translate(monster.shape),
            label_id="shape",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab7, List)
        lab7.translate(fix_width(width, 0.65), fix_height(height, 0.35))
        # species
        lab8 = menu.add.label(
            title=monster.category,
            label_id="species",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab8, List)
        lab8.translate(fix_width(width, 0.50), fix_height(height, 0.40))
        # taste
        tastes = T.translate("tastes") + ": "
        cold = T.translate("taste_" + monster.taste_cold)
        warm = T.translate("taste_" + monster.taste_warm)
        lab9 = menu.add.label(
            title=tastes + cold + ", " + warm,
            label_id="taste",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab9, List)
        lab9.translate(fix_width(width, 0.50), fix_height(height, 0.45))
        # capture
        doc = formula.today_ordinal() - monster.capture
        lab10 = menu.add.label(
            title=T.format("tuxepedia_capture", {"doc": doc}),
            label_id="capture",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab10, List)
        lab10.translate(fix_width(width, 0.50), fix_height(height, 0.50))
        # hp
        lab11 = menu.add.label(
            title=T.translate("short_hp") + ": " + str(monster.hp),
            label_id="hp",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab11, List)
        lab11.translate(fix_width(width, 0.80), fix_height(height, 0.15))
        # armour
        lab12 = menu.add.label(
            title=T.translate("short_armour") + ": " + str(monster.armour),
            label_id="armour",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab12, List)
        lab12.translate(fix_width(width, 0.80), fix_height(height, 0.20))
        # dodge
        lab13 = menu.add.label(
            title=T.translate("short_dodge") + ": " + str(monster.dodge),
            label_id="dodge",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab13, List)
        lab13.translate(fix_width(width, 0.80), fix_height(height, 0.25))
        # melee
        lab14 = menu.add.label(
            title=T.translate("short_melee") + ": " + str(monster.melee),
            label_id="melee",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab14, List)
        lab14.translate(fix_width(width, 0.80), fix_height(height, 0.30))
        # ranged
        lab15 = menu.add.label(
            title=T.translate("short_ranged") + ": " + str(monster.ranged),
            label_id="ranged",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab15, List)
        lab15.translate(fix_width(width, 0.80), fix_height(height, 0.35))
        # speed
        lab16 = menu.add.label(
            title=T.translate("short_speed") + ": " + str(monster.speed),
            label_id="speed",
            font_size=15,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab16, List)
        lab16.translate(fix_width(width, 0.80), fix_height(height, 0.40))
        # description
        lab17 = menu.add.label(
            title=monster.description,
            label_id="description",
            font_size=18,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab17, List)
        lab17.translate(fix_width(width, 0.01), fix_height(height, 0.56))
        # evolution
        lab18 = menu.add.label(
            title=evo,
            label_id="evolution",
            font_size=18,
            wordwrap=True,
            align=locals.ALIGN_LEFT,
            float=True,
        )
        assert not isinstance(lab18, List)
        lab18.translate(fix_width(width, 0.01), fix_height(height, 0.76))

        # open evolution monster
        def change_state(state: str, monster_slug: str) -> MenuGameObj:
            element = db.lookup(monster_slug, table="monster")
            return partial(
                self.client.push_state, state, kwargs={"monster": element}
            )

        # evolution monsters buttons
        f = menu.add.frame_h(
            float=True,
            width=fix_width(width, 0.95),
            height=fix_width(width, 0.05),
            frame_id="evolutions",
        )
        f.translate(fix_width(width, 0.02), fix_height(height, 0.80))
        f._relax = True
        # removes duplicates in evolutions
        player = local_session.player
        elements = []
        for ele in monster.evolutions:
            if ele.monster_slug in player.tuxepedia:
                elements.append(ele.monster_slug)
        no_duplicates = sorted(set(elements))
        labels = [
            menu.add.button(
                title=f"{T.translate(ele).upper()}",
                action=change_state("JournalInfoState", ele),
                align=locals.ALIGN_LEFT,
                font_size=15,
                selection_effect=HighlightSelection(),
            )
            for ele in no_duplicates
        ]
        for no_duplicates in labels:
            f.pack(no_duplicates)
        # image
        new_image = pygame_menu.BaseImage(
            tools.transform_resource_filename(monster.front_battle_sprite),
        )
        new_image.scale(prepare.SCALE, prepare.SCALE)
        image_widget = menu.add.image(image_path=new_image.copy())
        image_widget.set_float(origin_position=True)
        image_widget.translate(
            fix_width(width, 0.20), fix_height(height, 0.05)
        )
        # tuxeball
        tuxeball = pygame_menu.BaseImage(
            tools.transform_resource_filename(
                f"gfx/items/{monster.capture_device}.png"
            ),
        )
        capture_device = menu.add.image(image_path=tuxeball)
        capture_device.set_float(origin_position=True)
        capture_device.translate(
            fix_width(width, 0.50), fix_height(height, 0.445)
        )

    def __init__(self, monster: Monster) -> None:
        width, height = prepare.SCREEN_SIZE

        background = pygame_menu.BaseImage(
            image_path=tools.transform_resource_filename(
                "gfx/ui/item/tux_info.png"
            ),
            drawing_position=POSITION_CENTER,
        )
        theme = get_theme()
        theme.scrollarea_position = locals.POSITION_EAST
        theme.background_color = background
        theme.widget_alignment = locals.ALIGN_CENTER

        super().__init__(height=height, width=width)

        self.add_menu_items(self.menu, monster)
        self.repristinate()

    def repristinate(self) -> None:
        """Repristinate original theme (color, alignment, etc.)"""
        theme = get_theme()
        theme.scrollarea_position = locals.SCROLLAREA_POSITION_NONE
        theme.background_color = BACKGROUND_COLOR
        theme.widget_alignment = locals.ALIGN_LEFT
