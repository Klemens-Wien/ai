# KAMI skincare – private App (Flutter, iOS & Android)

Eine private, **inoffizielle** App für den Shop [kami-skincare.com](https://www.kami-skincare.com),
ausschließlich zur persönlichen Nutzung. Sie wird nicht veröffentlicht.

- Marke, Texte und Bilder gehören KAMI skincare.
- Bilder und das Logo werden zur Laufzeit von Shopifys CDN geladen.
- Shop-Texte werden lokal mit `tool/update_content.py` erzeugt und **nicht** ins Repository eingecheckt.
- Bestellungen laufen über den offiziellen Shopify-Checkout.

## Schnellstart

```bash
cd kami_app
python3 tool/update_content.py   # Shop-Inhalte nach assets/data/ laden (einmalig / bei Bedarf)
flutter pub get
flutter run                      # iOS-Simulator, Android-Emulator oder Gerät
flutter test                     # Logik-Tests (Quiz, Erinnerungen, Warenkorb, Katalog)
```

- **Flutter:** Getestet mit Flutter 3.50 / Dart 3.14.
- **iOS:** Braucht einen Mac mit Xcode.
- **Android:** Braucht ein Android-SDK mit `compileSdk` 37.

## Funktionen

| Bereich | Was es kann |
|---|---|
| Start | Hero mit Parallax, Laufband, aktuelles Angebot, Bestseller, Vorteile, Kategorien, Story, Quiz-Teaser, Ärzt:innen-Stimmen, Bewertungen, Blog, Newsletter |
| Shop | Kategorien (Neurodermitis, Psoriasis, trockene Haut, Narben, Kopfhaut, Anti-Aging, Auas), Suche, Sortierung, Hero-Animation zum Detail |
| Produkt | Galerie, Preis/Rabatt, Varianten, Menge, Tabs *Details / Anwendung / Inhaltsstoffe*, Erinnerung einrichten |
| Warenkorb | Lokal gespeichert, Fortschritt bis zum Gratisversand ab 60 €, Gutscheincode, „Zur Kasse“ öffnet den Shopify-Checkout über einen Cart-Permalink |
| Berater | 5 Fragen, Empfehlung nach den FAQ-Regeln von KAMI; Babys bekommen bewusst keine Empfehlung (EU-Kosmetik-VO) |
| Routine | Lokale Erinnerungen (Vorlagen aus den Anwendungstipps), Zyklus „3 Wochen an / 1 Woche Pause“, Tages-Checkliste, Serie |
| Mehr | Blog, FAQ, Bewertungen, Inhaltsstoffe, Kontakt (Shop-Formular oder Mail), Newsletter mit 10 %, Hell/Dunkel/Auto |

Preise und Blog werden live geladen (`/products.json`, `/blogs/kami-blog.atom`).
Ohne Netz nutzt die App den lokalen Snapshot.

## Struktur

```
lib/
├── app.dart, main.dart
├── core/          constants, theme (KAMI Farben + Light/Dark), router, utils
├── data/          models, repositories (Shopify JSON + Snapshot, Formulare), providers
├── shared/widgets Produktkarte, Bild mit Shimmer, Logo, Animationen, HTML-Renderer …
└── features/      home · catalog · product · cart · quiz · routine · content · newsletter · settings · shell · splash
tool/              update_content.py (lädt Seiten) + build_snapshot.py (erzeugt assets/data/*.json)
```

## Design

Die Farben stammen aus dem Theme-CSS der Website:
- Lila `#9989FE`
- Zartlila `#F0ECFE`
- Waldgrün `#003E37` / `#006144`
- Creme `#F3EEEA`
- Rosé `#F4E4E3`

Schriften:
- **Überschriften:** Cormorant Garamond, als freie Alternative zu *Saol Display*.
- **Fließtext:** Arimo, wie im Shop.

State Management mit Riverpod, Navigation mit go_router.
