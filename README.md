# A Tchoung té
> Langue [Yemba](https://fr.wikipedia.org/wiki/Yemba) siginifiant association/groupe en français

L'objectif du projet est de de fédérer les métadonnées de toutes les associations camerounaises de France afin de les rendre plus accessible à la communauté.
 

## Contexte fonctionnel

[Vidéo de présentation](https://peertube.stream/w/qmMMLyMbzAU8HWWAk1LAQJ)


## Contexte technique

Si vous êtes ici, c'est que vous intéressez par un déploiement maison de la solution. Suivez le guide :) !


### Prérequis

* Avoir un minimum de compétence sur le cloud AWS et Terraform
* terraform, awscli
* Avoir les accès admin sur une carte [Gogocarto](https://gogocarto.fr/projects)


### Déploiement

Sur AWS:  
  ```
    pushd infra ; terraform apply && popd
    pushd html ; aws s3 cp html/ s3://tchoung-te.mongulu.cm --recursive
  ```