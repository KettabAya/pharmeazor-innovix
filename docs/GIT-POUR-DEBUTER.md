# Git, pour débuter

Quatre commandes suffisent. Ce guide ne dit rien de plus.

---

## Une seule fois : récupérer le projet

Ouvrez un terminal, placez-vous là où vous voulez mettre le dossier, puis :

```bash
git clone https://github.com/KettabAya/pharmeazor-innovix.git
```

```bash
cd pharmeazor-innovix
```

Un dossier `pharmeazor-innovix` apparaît. **Vous ne referez jamais ça.**

### Si vous l'avez déjà cloné avant le renommage

Le dépôt s'appelait `pharmeazor.` avec un point. Il suffit de corriger l'adresse :

```bash
git remote set-url origin https://github.com/KettabAya/pharmeazor-innovix.git
```

---

## Chaque fois que vous commencez : récupérer le travail des autres

```bash
git pull
```

**Faites-le avant de toucher à quoi que ce soit.** Sans ça, vous travaillez sur
une version périmée, et vous aurez des conflits à démêler plus tard.

---

## Chaque fois que vous avez fini : envoyer votre travail

Trois commandes, dans cet ordre.

### 1. Choisir ce que vous envoyez

```bash
git add nom-du-fichier.py
```

Pour tout envoyer d'un coup :

```bash
git add .
```

Le point veut dire « tout ce qui a changé ».

### 2. Enregistrer, avec une phrase qui dit quoi

```bash
git commit -m "ajout du calcul des embeddings"
```

Cette phrase, c'est ce que vos coéquipières liront. Écrivez ce que vous avez
fait, pas « update » ni « fix ».

### 3. Envoyer

```bash
git push
```

C'est seulement à ce moment-là que votre travail arrive sur GitHub.

---

## Le cycle complet, en résumé

```bash
git pull                              # avant de commencer
# ... vous travaillez ...
git add .
git commit -m "ce que j'ai fait"
git push                              # quand vous avez fini
```

---

## Quand ça coince

### « Updates were rejected »

Quelqu'un a poussé avant vous. Récupérez son travail, puis renvoyez le vôtre :

```bash
git pull
```

```bash
git push
```

### « Please tell me who you are »

Git ne sait pas qui vous êtes. Une seule fois :

```bash
git config --global user.name "Votre Nom"
```

```bash
git config --global user.email "votre.email@example.com"
```

Utilisez **l'adresse de votre compte GitHub**, sinon vos commits ne vous seront
pas attribués et votre travail n'apparaîtra pas dans le panneau Contributors.

### « CONFLICT »

Deux personnes ont modifié le même endroit du même fichier. Git ne peut pas
choisir à votre place.

Ouvrez le fichier. Vous y verrez :

```
<<<<<<< HEAD
votre version
=======
celle de l'autre
>>>>>>>
```

Gardez ce qu'il faut, **effacez les trois lignes de marquage**, puis :

```bash
git add le-fichier
```

```bash
git commit -m "résolution du conflit"
```

### Je ne sais plus où j'en suis

```bash
git status
```

Cette commande dit toujours ce qui se passe : ce qui a changé, ce qui est prêt
à partir, si vous êtes en retard sur les autres.

---

## La règle qui évite 90 % des problèmes

**Dites dans le groupe quel fichier vous ouvrez, avant de l'ouvrir.**

Deux personnes qui touchent des fichiers différents ne se gênent jamais. Deux
personnes sur le même fichier, c'est un conflit assuré.

La semaine du 10 novembre, deux d'entre nous ont écrit le même script le même
soir. Trois minutes de message auraient suffi à l'éviter.

---

## Ne poussez jamais

- votre clé API (elle va dans `.env`, qui est ignoré par git)
- les fichiers de `data/raw/` (trop lourds, et ignorés)
- le dossier `.venv/`

Si `git status` vous montre des centaines de fichiers, c'est que l'un de ces
dossiers s'est glissé dedans. **Ne poussez pas**, demandez d'abord.
