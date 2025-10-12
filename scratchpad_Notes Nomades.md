#nand
2 bits : nombre de bits en dessous (3 en v2 ?)
```
01
```
`01` donc 1... Mais comme 0 bits ça veut rien dire (? (temporel ?)) c'est 1+1 donc 2 bits

4 × 2 bits :
- Nombre de circuits
- Nombre d'entrée max
- Nombre de sorties max
- Nombre de composants max
```
01 00 00 00
```
`01` donc 1... Donc 1+1 (?) circuits : 2
`00` donc 0... Donc 0 + 2 (1 entrée n'a pas de sens (t ?)) 2 entrée max
`00` donc 0... Donc 0+1 sortie max
`01` donc 1... Donc 1+1 sous composants max

NOT 
Circuit metadata :
- Id 2 circuits + 1 POUR 
- Nand donc 2 bits
- Nb sous circuits : 1 bit donc
```
01 0
```
``
01 = id 1
0 =  0 + 1 composants 

Composition :  × n donc × 1 composant
- id : 2 bits donc
- × m connexions = dictionnaire\[id\] (in + out) + à la toute fin × o sorties : somme de cts_dict\[id\] + 1 connexions...Compliqué : plusieurs passes ? Dans ce cas, qu'est ce qui m'empêche de faire plusieurs passes partout ? Sûrement pas possible pour les metadata ? Ici : 1 composant (nand) avec 2 entrée + 1 sorties donc = 3 connexion pour lui... Mais comme que 1 sortie -1 
    -  pour input nand : 1 bit provenance : input ou composant... Mais là que 1 composant donc 0
    -  pour input nand : x bits input index : 
        - soit nb sortie donc 1 bit si input
        - soit nb composants donc ici 1 bit
    - pour output nand : output if donc 1-1 0 bit
    - pour output circuit :
        - id composant ici que 1 donc 0
        - idx out : composant a que 1 donc 0
```
00
```
00 nand : sous entendu provenance 1 entrée donc 0 bit, sous entendu que 1 idx donc 0 bit, sous entendu 1 output nand avec 1 seul composant donc 0 bit idx, sous entendu 1 sortie donc 0 bit idx

AND metadata
```
10 1
```

10 circuit n° 2
1 : 2 composants

AND premier composant
```
00  00 01
```
00 : nand
In 0 : 0 : provenance in général.
In 0 : 0 : in general 0
In 1 : 0 provenance in general
In 1 : 1 : in général 1

AND deuxième composant
```
01 1 
```
01 : NOT
In 0 : provenance 1 : composant. Sous entendu : un seul autre composant (comme pas de boucle (t ?)) donc 0 bit

OUT général : 1 connexion
```
1
```
1 : 2e composant. Sous entendu que 1 out à NOT donc 0 bit pour idx out composant. 


Total : 28 bits entre 3 et 4 octets pour NOT + AND

OR

```
11 10
```
ID 3 3 composants

1 er nand
```
00  00 00
```

2e nand

```
00  01 01
```

3 nand

```
00  10 11 
```

Out

```
10 
```

On ajoute 24 bits = 24 + 28 = 52 bits = entre 6 et 7 octets : ex: AAAAAAA

Comme 3 composants, on ajoute + 2 bits comme il faut 2 bits pour le nb de sous composants, donc 54 bits, donc plus 7 que 6 octets

---

n composant

log(n) bits par composant = b

 i entrées générale : 1 bit n
 j entrée circuit : b+1 bits m

i * 1 + (b+1) * j < b * (i+j)

```
i + jb + j < bi + bj
i + j < bi
j < bi - i
j < i (b-1)
```

j + i > log(n) * i
i < j / (log(n) - 1)
 
  i * (b-1) < j

---

i in *venant de* de circuit
j in *venant de* composants
n composants donc log2(n) = b bits d'index

Note : on ignore les effets de seuils, on suppose que n+1 composants (+1 car in de circuit) donne toujours b bits)

Si pas de raccourci provenance (i.e 0 pour indiquer les ins) :
b * (i+j) = le nombre de bits totaux dédiés à la provenance

Si raccourci provenance
1 * i + (b+1) * j = le nombre de bits totaux dédiés à la provenance
Explication :
- 1 bit * i inputs venant circuits (car 1 bit de provenance = 0)
- b+1 bits * j inputs venant de composants (car 1 bit de provenance = 1 + b pour l'index)

Donc le raccourci est valable si :
i + j * (b+1) < (i + j) * b
i + bj + j < bi + bj
i + j < bi
j < bi - i
j < i * (b-1)

Bits économisés :
i * (b-1) - j

Exemple :

Pour 2 bits de composants :
j < i * 1 : il faut qu'on ait strictement moins de in venant de composants que de in venant de circuit
Pour OR par exemple avec 3 NAND :
- in venant de composants = 3
- in venant de circuit = 4
3 < 4 * 1 OK !
1 bit économisé

Pour 3 bits de composants :
j < i * 2
Pour Full-Adder avec 2 ANDs, 2 XOR, 1 OR :
- in venant de composants = 5
- in venant de circuits = 6
5 < 6 * 2 OK !
7 bits économisés

---

Notes :

Le raccourci de provenance 1-bit peut provenir de n'importe quel composant. Même si dans notre cas, le "composant" sont les ins du circuit. Le feeling général est de trouver le "composant" dont les sorties sont le plus référencées. Donc très souvent les inputs. Mais peut-être qu'il existe un circuit spécial ?
Le leverage est énorme *2 jusqu'à 8 composants. Il faut que la somme totale de tous les autres inputs de composants soit 2 * supérieur au inputs du circuits
Et * 3 pour 16 composants !

Mais ensuite, gros problème pour savoir *quel* composant est spécial, et surtout comment le définir sans trop de bits ?

Si on inverse le sens des circuits (là on définit les entrées des composants + des outputs, on pourrait faire dans l'autre sens : définir les outputs des composants + des ins), le raccourci provenance serait dans l'autre sens

Note : À quoi ressemble une provenance raccourcie à 2 bits ? 4 entrées possibles, je vois pas trop. Ça peut aussi être 3 entrées : (00, 01 et 1), mais dans ce cas, que mettre dans les autres entrées ? Surtout en hardcodé ? Ou, si pas en hardcodé, comment les définir ?

---

Pinaillage :

Pour 1 bit de composants : Jamais le cas...
Pour NOT avec un 1 NAND
- in venant de composant = 1
- in venant de circuit = 2
1 bit perdu...
(NAND in ; circuit out)
(0_ 0_ ; 1x_) vs (x_ x_ ; y_)
... Mais est-ce vraiment le cas ? 1 composant = sous-entendu, on peut skip la provenance

Pour 1 AND avec 1 NAND et 1 NOT
- in venant de composant = 2
- in venant de cicruits = 2
2 bits perdus...
(NAND in ; NOT in ; circuit out)
(0_ 0_ ; 1x_ ; 1y_) vs (x_ x_ ; y_ ; z_)
... Pareil, est-ce le cas ? avec les sous-entendus

---

Input :
- possible d'enlever le nb de bits d'idx d'in si les ins sont dans l'ordre. Ex : composant 1 : in 1 et 2 donc idx 0 et 1. Idx 1 : tous les prochains in ont un idx sur 2 bits. Composant 2 : in 1 et 3 donc idx 00 et 10.
- pb : à partir d'un circuit, réorganiser les ins pour mettre dans l'ordre
- ne pas oublier mettre la provenance avec
- est-ce qu'un ordre est possible ?
- mettre un bit qui active ou non ce comportement
- peut être relou pour les in. Ex : adders n bits : a0 b0 a1 b1 a2 b2 : interleaved
Input + Fils intermédiaires :
- Même concept qu'au dessus, sauf que ça s'applique à tous les fils 
- On a un nb d'input, mais pas de provenance
- Pour chaque circuit : les inputs commencent sur n bits, et dès qu'un nouveau circuit arrive on ajoute un nouveau fil. ex: full adder :
	- 3 inputs, donc 2 bits
	- xor0 in0 in1 (101 00 01) ← Maintenant 11 est le out de x0r0
	- and0 in0 in1 (010 00 01) ← Maintenant fils en 3 bits, 100 est le out de and0
	- xor2 out0xor0 in2 (101 011 010) ← 101 out de xor2
	- and1 out0xor0 in2 (010 011 010) ← 110 out and1
	- or0 out0and0 out0and1 (010 100 110)
	- = 3* 5 + 3* 2 + 2 * 2 =15 + 6 + 4 = 25
	- out : 25 + 3 + 3 = 31
- Permet d'avoir la concentration complète de tous les bits de fils **et** la provenance **et** la progressivité du nb de bits
- Xor : 
	- wires
		- 000 0 1 : 000 00 10 ; 000 01 10 ; 000 011 100 ; 101 = 29
	- v0 (intermédiaire (pas naïf, pas trop malin))
		- 000 00 01 ; 000 00 100 ; 000 01 100 ; 000 101 110 ; (11) = 31 (33) ← sous entendu 1 out pour les composants xor
		- 000 00 01 ; 000 00 1 ; 000 01 10 ; 000 101 110 ; (11) =  29 (31) ← idées similaire de progressivité de l'idx des composants
- Note : pour 2bits-adder et 4bits-adder, la v1 semble être bien meilleure, en utilisant un idx comp progressif + input progressif
- Question : y a-t-il un moyen de faire qqch comme la provenance ? ça rajoute un bits partout, mais qu'est ce que ça peut économiser ?
- Metadata : n_comp n_in n_out
- Est-ce qu'être malin avec l'encoding v0 peut rattraper ? Est-ce qu'on peut aussi être malin avec cette versions wirings ?
Output :
- possible de juste pas lister les output si : sous entendu on parcourt les composants 1 à 1 et en sous boucle les out non utilisées.
- problème : réorganiser + toujours possible ? Non, pas tj possible : composant n à 1 out qui va à un in d'un composant m *et* au out général
- bit de set ou non cette option voir bit à répétition pour dire "ok, next"
- relou car difficile de choisir l'ordre des outs : il faut réfléchir au global (ex : ordre des outs dans le full adder peut rendre en out 4 bits : c0 c1 c2 d c3)

Note : à voir le focus. D'un côté on a le fait de devoir spécifier d'une façon très précise pour avoir un encoding optimal. De l'autre, avoir une plus grosse flexibilité pour définir les circuits mais moins condensé. Ou passer du cas 2 vers le cas 1 via des transformations. Mais dans ce cas, pour cet exemple, ordre in et out pas respectée... Mais est-ce grave si on veut juste **un** circuit ?

---

https://bsky.app/profile/righto.com/post/3ljg2vnr3vk2l

> Multiplying in base 8 means each term gets multiplied by 0 through 7. Multiplying by 2 or 4 is easy, just shift the number. A trick for ×7:  multiply by 8 and subtract 1×. (This is Booth's algorithm.) For ×6, multiply by 8 and subtract 2×. But what about ×3? It needs a special circuit. 3/N

---

Idées de CPU à implémenter :
- Sebastian Lague
- 8bits ben eater ?
- https://github.com/floooh/chips/tree/master/chips
- CHIP-8
- nand2tetris
- https://en.wikipedia.org/wiki/Stack_machine
- https://users.ece.cmu.edu/~koopman/stack_computers/chap4.html

---

/r/nand2tetris

/r/Turingcomplete

/r/theoreticalcs

/r/compsci

https://github.com/ArhanChaudhary/NAND

https://gitlab.com/x653/nand2tetris-fpga/

---

Ressources formelles et académiques :

- https://www.reddit.com/r/cpudesign/comments/1ep6inv/literature/