from datetime import date

category_dict = {
    "Model Kit": {
        "Dragon Ball Figure Rise": [],
        "Sword Art Online Figure Rise": [],
        "Exa Gear Kotobukiya": [],
        "Evangelion Model Kit": [],
        "Patlabor Model kit": [],
        "Navi di One Piece": [],
        "Gunpla Gundam Model Kit": [],
        "Accessori Model Kit": [],
        "Digimon Model Kit": [],
    },
    "FIGURES": {"Statue e Statuette": [], "Repliche Veicoli": [], "Action Figures": []},
    "FUNKO": {"Funko POP": [], "Funko Peluche": [], "Funko Pocket Keychain": [], "Funko Calendari Avvento": []},
    "LEGO": {
        "Lego Duplo": [],
        "Lego Minecraft": [],
        "Lego Star Wars": [],
        "Lego VIDIYO": [],
        "Lego Super Heroes": [],
        "Lego Technic": [],
        "Lego Disney": [],
        "Lego City": [],
        "Lego Classic": [],
        "Lego Harry Potter": [],
        "Lego Ninjago": [],
        "Lego Super Mario": [],
        "Lego Speed Champions": [],
        "Lego Jurassic World": [],
        "Lego Marvel": [],
        "Lego Avengers": [],
        "Lego Batman": [],
        "Lego ART": [],
        "Lego DOTS": [],
        "Lego Creator": [],
        "Lego Architecture": [],
        "Lego DC": [],
        "Lego Friends": [],
        "Lego Minifigures": [],
        "Lego Minions": [],
        "Lego Stranger Things": [],
        "Lego Calendari Avvento": [],
    },
    "VIDEOGIOCHI E CONSOLE": {
        "Giochi Console e Accessori per Nintendo Switch": [
            "Amiibo Nintendo",
            "Giochi per Nintendo Switch",
            "Console Nintendo Switch",
            "Accessori per Nintendo Switch",
        ],
        "Retrogaming e Mini Console": [],
        "Giochi Console e Accessori per XBox Series X e S": [
            "Giochi per XBox Series X e S",
            "Console XBox Series X e S",
            "Accessori per XBox Series X e S",
        ],
        "Giochi Console e Accessori per XBox One": [
            "Giochi per XBox One",
            "Console XBox One",
            "Accessori per XBox One",
        ],
        "Giochi Console e Accessori per PlayStation 4": [
            "VR PlayStation 4",
            "Giochi per PlayStation 4",
            "Console PlayStation 4",
            "Accessori per PlayStation 4",
        ],
        "Giochi Console e Accessori per PlayStation 5": [
            "Giochi per PlayStation 5",
            "Console PlayStation 5",
            "Accessori per PlayStation 5",
        ],
        "Giochi e Accessori per PC": [
            "Giochi per PC",
            "Accessori di Gioco per PC",
            "Portatili Laptop Gaming",
            "PC Desktop Gaming",
            "Monitor Gaming",
            "Componenti PC Gaming",
        ],
    },
    "DVD E BLU-RAY FILM E SERIE TV": {"BLU-RAY": [], "DVD": []},
    "Carte Collezionabili": {
        "Carte Naruto": [],
        "Carte Yu-Gi-Oh": [],
        "Carte Magic the Gathering": [],
        "Carte Pokemon": [],
        "Carte Dragon Ball": [],
        "Carte Cardfight Vanguard": [],
    },
    "Giochi da Tavolo Board Game": {
        "Giochi da Tavolo": [],
        "Giochi di Ruolo": [],
        "Giochi di Carte": [],
        "Accessori Giochi da Tavolo": [],
    },
    "Peluche e Giocattoli": {"NERF": [], "Giocattoli": [], "Peluche": [], "Puzzle": []},
    "Gadget": {
        "Gadget Geek Nerd": [],
        "Poster": [],
        "Repliche Armi e Accessori": [],
        "Tappeti e Zerbini": [],
        "Tazze": [],
        "Salvadanai": [],
        "Agende e Quaderni": [],
        "Pasta Intelligente": [],
        "Portachiavi": [],
        "Lampade": [],
        "Teli da mare e Asciugamani": [],
        "Cable Guy": [],
    },
    "Abbigliamento": {
        "Cappelli": [],
        "Accessori Abbigliamento": [],
        "Felpe": [],
        "Magliette": [],
        "Borse e Tracolle": [],
    },
    "Fumetti": {},
    "Libri e Guide Strategiche": {"Libri di Cucina": [], "Guide Strategiche": []},
}

cat_map = {
    "VIDEOGIOCHI E CONSOLE": "Videogiochi",
    "DVD E BLU-RAY FILM E SERIE TV": "Film e Serie TV",
    "FIGURES": "Figures",
    "Gadget": "Gadget",
    "Model Kit": "Modellismo e Model Kit",
    "Peluche e Giocattoli": "Giochi",
    "Abbigliamento": "Abbigliamento",
    "Libri e Guide Strategiche": "Libri e Fumetti",
}


def edit_create_category(new_name, model_name, parent_id=None):
    existing_cat = self.env[model_name].search([("name", "=", new_name)])
    if existing_cat:
        return existing_cat.id

    search_name = cat_map.get(new_name, new_name)
    cat = self.env[model_name].search([("name", "=", search_name)])
    if not cat:
        print(f"Categoria da creare: {new_name}")
        cat = self.env[model_name].create(
            {
                "name": new_name,
                "parent_id": 1 if not parent_id else parent_id,
                "create_uid": 2,
                "write_uid": 2,
                "create_date": date.today(),
                "write_date": date.today(),
            }
        )
        print(f"Categoria creata: {cat.name}")
    else:
        print(f"Categoria da rinominare: {cat.name} => {new_name}")
        cat.name = new_name
        if parent_id:
            cat.parent_id = parent_id
        print(f"Categoria rinominata in {cat.name}")

    print(f"Salvo nel DB")
    self._cr.commit()

    return cat.id


def migrate_category(model_name):
    for main_category, main_child in category_dict.items():
        main_category_id = edit_create_category(main_category, model_name, None)
        if not main_child:
            continue
        for second_category, second_child in main_child.items():
            second_category_id = edit_create_category(second_category, model_name, main_category_id)
            if not second_child:
                continue
            for third_category in second_child:
                edit_create_category(third_category, model_name, second_category_id)


migrate_category("product.category")
migrate_category("product.public.category")
