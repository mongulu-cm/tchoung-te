# A Tchoung té
> Langue [Yemba](https://fr.wikipedia.org/wiki/Yemba) siginifiant association/groupe en français

L'objectif du projet est de de fédérer les métadonnées de toutes les associations camerounaises de France afin de les rendre plus accessible à la communauté.
 

## Contexte fonctionnel

[Vidéo de présentation](https://peertube.stream/w/qmMMLyMbzAU8HWWAk1LAQJ)


## Contexte technique

Si vous êtes ici, c'est que vous intéressez par un déploiement maison de la solution. Suivez le guide :) !


### Prérequis

* Avoir un minimum de compétence sur le cloud AWS et Terraform
* terraform, awscli,[pyspark](https://towardsdatascience.com/how-to-use-pyspark-on-your-computer-9c7180075617)
* Avoir les accès admin sur une carte [Gogocarto](https://gogocarto.fr/projects)
* Parcourir les [tutoriels Gogocarto](https://peertube.openstreetmap.fr/c/gogo_tutos/videos)


### Déploiement

Sur AWS:  
  ```
    pushd infra ; terraform apply && popd
    pushd html ; aws s3 cp html/index.html s3://tchoung-te.mongulu.cm/index.html
  ```

Puis éxécutez le notebook `filter-cameroon.ipynb` après voir installé les dépendances nécessaires:
  ```
    cd etl && pipenv sync
    jupyter lab
  ```

Enfin utilisez le fichier csv résultat comme source de donnée dans Gogocarto et personnalisez là.
Vous pouvez par exemple définir des icônes par catégorie(objet social) ; les notres étant dans `html/icons`.
> Celles-ci ont été construite à partir de ces icônes de bases https://thenounproject.com/behanzin777/kit/favorites/