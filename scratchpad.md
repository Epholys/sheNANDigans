#nand

# Ressources

1. https://google-research.github.io/self-organising-systems/difflogic-ca/
2. https://blog.startifact.com/posts/succinct/

# DOING

# Planning

[ ] Projet
    [ ] Réfléchir à une license alternative
        [ ] Regarder celles sur [tl;drLegal](https://www.tldrlegal.com/)
        [ ] [PolyForm](https://polyformproject.org/licenses/)
        [ ] [Komorebi](https://lgug2z.com/software/komorebi/)
    [ ] Porter sur le Web ? (voir WebAssembly)

[O] Environnement de développement
    [ ] VS Code
        [ ] Configurer ou apprendre les raccourcis 
            [ ] Raccourcis d'édition de code
            [ ] Raccourcis d'exécution de code + Compilation
    [ ] Pycharm
    [ ] Git
        [O] Aliases
        [X] Diff
    [O] Python
        [O] Ruff
            [X] Auto format
            [ ] Auto fix
        [X] Tests
            [X] Passer à pytest            
        [ ] Passer de venv à uv
        [ ] Gérer les requirements pip au propre

[O] Qualité du code
    [X] Commentaire : classe, méthode, code
    [X] Meilleur nommage
    [X] Chercher refacto
    [X] En apprendre plus du @dataclass(frozen=True)
    [ ] Voir les TODOs

[O] Tests autos
    [X] Tester les circuits : leur fonction (AND, Adder, etc)
    [X] Tester l'encodage avec les circuits en round-trips
    [X] Tester l'encodage avec les bits en round-trip
    [O] Factoriser les tests autos fonctionnels des circuits numériques (adders)
        [X] Première passe : super OK !
        [X] Gros nettoyage suite à la parallélisation
    [ ] Tests auto du code : sur les classes et méthodes
    [ ] Tests autos-autos : à partir d'un .nand, décoder les circuits, générer une table de véritée, round trip puis vérifier

[O] Accélérer la simulation
    [O] Rapidifié la simulation : Faire du profiling
        [X] Ordre topologique
        [X] Séparation en v.debug et v.fast :
            [X] Wire, Reset, & Simulation
            [X] Définir ce qu'est le debug. Sans ou avec ordre topo ? Si sans, was_/can_ + simulate_slow à suppr ?.
            [X] Bare Wire, Optimization, Conversion
        [?] Accélérer les conversions Wire et WireState int <-> bool
            [?] Profiler WireFast & WireDebug ?
            [ ] \_\_slots\_\_ ?
        [ ] Pistes avancées : Voir ChatGPT
            [ ] Simuler en // avec l'ordre topologique
            [ ] Simuler en // si on a des blocs bien distincts dans les circuits
            [ ] Vectorization a/c NumPy/PyTorch/CuPy :
                [ ] Avec des listes d'index créer deux listes a et b, faire o = ~(a & b), puis idem pour les résultats
                [ ] Comme ci-dessus, mais pas faire des listes mais des nombres et utiliser les bits
            [ ] Descendre de niveau avec du C, ou Cython
            [ ] Appliquer ces techniques pour faire de la simulation en // (ex: tests autos : voir ci-dessous)
    [O] Les tests en particulier
        [X] Paralléliser via pytest
        [O] Paralléliser big n-bits
            [X] ProcessPoolExecutor :  
                [X] J'ai persévéré : OK !
                [O] Fine-tune Windows avec profiling (cProfile + hyperfine + autre ?) : tenté, à revoir plus tard, regarder les commentaires
            [ ] Vérifier pour *nix avec Threads

[O] Créer encodage / décodage /testing Kolmogorov-esque des circuits
    [O] Encodage à la force de mon cerveau (avec aide LLM)
        [O] Encodage principal
            [X] Première étape d'encodage simple (niveau octet)
                [X] Encodage
                    [X] Vérification manuelle
                [X] Décodage
                [X] Vérification
                    [X] Round Trip
                    [X] Tests auto
            [X] Réduction au niveau des bits
            [ ] Optimisation locale : les "sous-entendus". ex : "on sait que tel circuit a un seul out, donc pas besoin de préciser"
            [ ] Optimisation "conditionnelle" :
                - ex : si les inputs sont dans "l'ordre d'apparition", les coder comme 0 puis 00 01 puis 000 001 010 011 etc
                - ex : si les outputs sont dans "l'ordre d'apparition", juste ne pas les mettre
        [ ] Révolution encodage :
            1. Applatir le circuit : full nand
            2. Tester l'encoding actuel dessus
            3. Optimiser pour du full nand
            [ ] Implémentation de base
            [ ] Implémentation bit-packed
            [ ] Modification encoding : mettre les inputs en premier avec ordre d'apparition puis seulement compléter les nands restant avec index ?
        [ ] Métadonnées optionnelles 
    [O] Testing du nombre de bits des encodages
        [X] encoding_stats.py
        [ ] Tester comment la définition des circuits influence la taille de l'encoding (ex: or → or2way → or4way → or8way vs or8way direct)
        [ ] Avoir des fichiers .nand de tests variés et indique les bits perdus/économisés
    [ ] Rechercher dans la littérature et projets existants :
        [ ] Check des codecs *dans ce domaine*
        [ ] *Algorithmes* de compression lossless classique : DEFLATE
        [ ] Lire https://solhsa.com/oldernews2025.html#ON-FILE-FORMATS (https://news.ycombinator.com/item?id=44049252) 
        [ ] Codecs existants (voir https://wiki.x266.mov/)(https://lobste.rs/s/mkpgoe/on_file_formats)
            [ ] Compressions : ZIP, 7z, XZ, Brotli, Zstandard, Zpaq
            [ ] Images : PNG, QOI
            - Talk CCC [More Than Just Quite OK – Data Compression Nerds Hate This One Trick ](https://media.ccc.de/v/eh22-8-more-than-just-quite-ok-data-compression-nerds-hate-this-one-trick#t=1809) 
                - PNG :
                    - Paletting : Est-ce que je peux avoir une liste de circuits avec index ? C'est un peu ce que je fais de base avec le nested non ? Et si on imagine pas des circuits mais des blocs, qui sont cherchés automatiquement ?
                    - Filtering (none, up, left, up-left, Paeth) : semble avoir une logique uniquement sur des scanlines. Y a-t-il moyen d'avoir des scanlines, d'image-ifier ?
                    - DEFLATE :
                        - LZ : dictionary-coding : référence en arrière : genre pour des def de circuits répétitifs (adder) ? Ou une liste récurrente d'input (1, 2, 3, 4) ou autre ?
                        - Huffman : ?
                        - En général, on peut tester de encoder puis de passer vers du zip/DEFLATE/autre pour voir ce que ça donne ?
                - QOI :
                    - Run : suite identique de pixels : pas vraiment appliquable
                    - Index sur un pixel précédent : ???
                    - Différence avec le pixel précédent : peut-être utile pour les suite d'inputs/outputs ?
                    - Full
                - Idées à retenir :
                    - Un format de fichier privilégie un ou plusieurs axes. Ex: vitesse, simplicité, taille, résistance à la corruption, latence, ... Dans mon cas, je suis sur la taille, mais à voir si je peux compromettre pour un peu plus de simplicité, de vitesse, ou de développement (ex: nested vs flat)
                    - Faire simple peut être un excellent compromis. Ex : QOI est très *très* simple et pourtant pas beaucoup plus gros que PNG tout en étant beaucoup plus rapide
                    - (Design by comittee pas ouf)
                - (Discussion HN)[https://news.ycombinator.com/item?id=43760099]) :
                    - "It serves as a good example that input modelling is very important, so much that QOI almost beats PNG in spite of very suboptimal coding"
                    - https://github.com/nigeltao/qoir/
                - https://github.com/ENDESGA/PEP Pour Pixel Art
        [ ] Data structures. Ex : "Succint data structure" (Lien 2)
        [ ] Encodage Machine Learning à la fbellard
    [ ] Tester avec des méthodes un peu abstraite sur la compression max possible (Kolmogorov)
        [X] Tester si compresser avec zip, 7zip, xz, etc réduit la taille : voir scratchpad_compression.py
        [ ] Se renseigner sur le calcul d'entropie
        [ ] Voir compsci/maths avec Shannon et la [V-Information](https://arxiv.org/pdf/2002.10689)

[O] Visualiser les circuits avec Graphviz
    [X] Premières vizs !
    [X] Options de viz
        [X] Upgrade
            [X] Box globale
            [X] Set les ins à gauche et outs à droite    
            [X] Permettre de s'arrêter à un niveau de récursion
                [X] S'arrêter
                [X] Mettre un colorscheme
        [X] Mettre en plus gras les lignes circuits ins → et ← circuits outs
    [X] Hyper-compacts : uniquement les NAND
            [X] v1 (merci Claude)
            [X] Refacto v1
            [X] Options : Alignement, ↓
            [X] Semi-compact : ajouter les clusters
    [ ] Améliorer Lisibilité
        [ ] Continuer à chercher dans les options graphviz (voir `_try_hard()`)
        [ ] Forcer les ins et outs dans l'ordre ?
        [ ] Gérer les nombres : plutôt que d'avoir n inputs, ou en a un : le nombre
        [ ] Voir algo existant networkx
    [ ] v2 :
        - penrose ? https://penrose.cs.cmu.edu/try/?examples=logic-circuit-domain/half-adder
        - D2 ? https://d2lang.com/

[ ] Vérification de la robustesse
    [ ] Implémentation : is_valid() et sanitize() ?
    [ ] Stress-test
        [ ] Reordering random
        [ ] Génération random ?
        [ ] Fuzzing ?
        [ ] Tests tous les inputs ?

[O] Application
    [O] Stateless ALU
        [O] nand2tetris Hack ALU
    [ ] Stack-based CPU
        [ ] [uxn](https://wiki.xxiivv.com/site/uxn.html) ?
    [ ] Voir ce que fait [howerj](https://github.com/howerj)
    [ ] Voir [Soft microprocessor](https://en.wikipedia.org/wiki/Soft_microprocessor) 
    [ ] Register-based CPU
        [ ] CHIP-8 ?
        [ ] 8080, 8086, NES ?
        [ ] Voir list de [floooh](https://floooh.github.io/tiny8bit-preview/)
        [ ] Eater https://eater.net/8bit/
        [ ] https://github.com/Shim06/PandesalCPU
    [ ] "Deep Differentiable Logic Gate Networks" (voir premier lien)
    [ ] Voir FGPA / Verilog / [Spade](https://spade-lang.org/) ?
    [ ] Programmer des trucs ?
        [ ] hex0, etc ?
        [ ] Apple 1's [Woz Monitor](https://www.sbprojects.net/projects/apple1/wozmon.php) ?

[ ] Usage avec ligne de commande
    [ ] DSL pour définir les circuits
    [ ] Encoder
    [ ] Exécuter

[ ] Optimisation automatisée des circuits
    [ ] Ordre des composants/inputs/outputs : voir optimisation "conditionnelle"
    [ ] "Analyse fonctionnelle"
        [ ] En regardant les `raw_`, on voir qu'on a des nand ⇒ nand ⇒ nand, qui est not ⇒ not , dans les circuits AND → OR, donc on peut simplifier
    [ ] "Factorisation en plusieurs fonctions".
        [ ] À partir d'une spec (ex : table de vérité), générer le.s circuits à partir de blocs élémentaires
        [ ] À partir d'un gros circuit, faire des blocs : Voir premier lien ou les `raw_.svg`
            Note : au vu de l'encodage actuel, je soupçonne (à vérifier) que pleins petits blocs est bien meilleur que quelques gros
        [ ] À partir d'un circuit existant, refaire des blocs

# Notes d'apprentissages

## Général

- Si tu vois que tu galères vraiment beaucoup sur une voie, c'est sûrement que c'est pas la bonne.
    - Exemple : graph_raw.py, 2025-03-09 : tu t'es trop basée sur graph.py avec une récursion pour prendre tous les ins/outs et essayer de les "collapser" avec les wires, et tu as trébuché de ouf entre les in outs globaux, les wirings... Alors que la version de Claude a juste une récursion pour chopper tous les nands, et des boucles imbriquées pour chopper les ids des fils.
    - Essayer de briser le "dark flow" et chercher une autre voix. Même si briser le dark flow veut juste dire d'arrêter pour aujourd'hui, ou du moins ce sujet, et consciemment explorer autre chose ensuite

## LLM

- Peut être super bon pour avoir une version premier jet qui fonctionne !
    - Ne pas hésiter à l'utiliser : j'ai passé 2h sans réussir et il a accompli ça en 2min ! (2025-03-09)
        - Note : peut-être que le fait d'avoir ma première version l'a aidé... Mais je pense pas vu son code
    - Nécessaire de passer derrière pour tout refactorer et mettre au propre
    - Faire des itérations sur le code généré ou existant n'est pas tout le temps une bonne idée, il s'embrouille de plus en plus
- Est souvent en retard sur les bonnes pratiques : lors des questions il indique des solutions qui sont souvent dépassées (Python 3.5 vs 3.12 (au pif))
- Point négatif ? 
    - Sa solution devient la base de l'algo, est-ce une bonne idée ?
    - Sur du code existant, sa solution est souvent bazardeuse
    - Nuances : c'est arrivé plusieurs fois que je lance Claude et qu'il pond un truc vraiment pas terrible, que je refasse tout... mais est-ce une mauvaise chose ? Si on est positif, on peut dire qu'on se rend compte que sa manière de faire est mauvaise, donc est-ce une perte de temps si on se rend compte d'un mauvais chemin à ne pas prendre ? En comparaison avec la perte de temps de coder un algo sans réussir
