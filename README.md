# A Tchoung té
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
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
## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/fabiolatagne97"><img src="https://avatars.githubusercontent.com/u/60782218?v=4?s=100" width="100px;" alt=""/><br /><sub><b>fabiolatagne97</b></sub></a><br /><a href="#tutorial-fabiolatagne97" title="Tutorials">✅</a></td>
    <td align="center"><a href="https://github.com/DimitriTchapmi"><img src="https://avatars.githubusercontent.com/u/15048420?v=4?s=100" width="100px;" alt=""/><br /><sub><b>DimitriTchapmi</b></sub></a><br /><a href="#tutorial-DimitriTchapmi" title="Tutorials">✅</a></td>
    <td align="center"><a href="https://github.com/pdjiela"><img src="https://avatars.githubusercontent.com/u/36527810?v=4?s=100" width="100px;" alt=""/><br /><sub><b>pdjiela</b></sub></a><br /><a href="#tutorial-pdjiela" title="Tutorials">✅</a></td>
    <td align="center"><a href="https://github.com/GNOKAM"><img src="https://avatars.githubusercontent.com/u/60141878?v=4?s=100" width="100px;" alt=""/><br /><sub><b>GNOKAM</b></sub></a><br /><a href="#tutorial-GNOKAM" title="Tutorials">✅</a></td>
    <td align="center"><a href="https://github.com/gttakam"><img src="https://avatars.githubusercontent.com/u/62386113?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Ghislain TAKAM</b></sub></a><br /><a href="#tutorial-gttakam" title="Tutorials">✅</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!