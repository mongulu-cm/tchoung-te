# A Tchoung té
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-11-orange.svg?style=flat-square)](#contributors-) <!-- ALL-CONTRIBUTORS-BADGE:END -->
[![Commitizen friendly](https://img.shields.io/badge/commitizen-friendly-brightgreen.svg)](http://commitizen.github.io/cz-cli/)

> [Yemba](https://fr.wikipedia.org/wiki/Yemba) language meaning association/group in French

The objective of the project is to federate the metadata of all Cameroonian associations in France to make them more accessible to the community. 

## Functional Context 

[Presentation video (in French)](https://peertube.stream/w/qmMMLyMbzAU8HWWAk1LAQJ)

If you want to do data analysis, the raw latest database of cameroonian association is accessible [here](https://lite.datasette.io/?csv=https://raw.githubusercontent.com/mongulu-cm/tchoung-te/main/etl/ref-rna-real-mars-2022-enriched-qualified.csv#/data/ref-rna-real-mars-2022-enriched-qualified). 

We also maintained a public dashboard to visualize associations [here
](https://metabase.mongulu.cm/public/dashboard/30534b6c-9a55-441a-8b86-168a2147869a#theme=night)

## Technical context

If you are here, it means that you are interested in an in-house deployment of the solution. Follow the guide :) !

### Prerequisites

* Create a Sourcegraph account and get credentials to use [CodyAI](https://www.youtube.com/watch?v=_csyHcEcxDA)
*  [Devspace](https://www.devspace.sh/) installed locally
* Have admin access on a [Gogocarto](https://gogocarto.fr/projects)
* Go through the [Gogocarto tutorials](https://peertube.openstreetmap.fr/c/gogo_tutos/videos)
* Locally install all tools ( `init` and `command` scripts from the [.gitpod.yml](.gitpod.yml) file **or** use a ready-made development environment on gitpod :

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/mongulu-cm/tchoung-te)


### Learn about this repo

* Gitpodcast: https://www.gitpodcast.com/mongulu-cm/tchoung-te
* Gitdiagram: https://gitdiagram.com/mongulu-cm/tchoung-te

### Deployment
  
Execute  `filter-cameroon.ipynb` et `enrich-database.ipynb` notebooks :
  ```
    pipenv shell
    secretsfoundry run --script 'python filter-cameroon.py'
  ```

Finally use the resulting csv file as a data source in Gogocarto and customize it.
You can for example define icons by category (social object); ours are in `html/icons`.
> These have been built from these basic icons https://thenounproject.com/behanzin777/kit/favorites/


### Update database

  ```
    csvdiff ref-rna-real-mars-2022.csv rna-real-mars-2022-new.csv -p 1 --columns 1 --format json | jq '.Additions' > experiments/update-database/diff.csv
    python3 main.py
  ```

### Start the chatbot

  ```
    cd etl/
    secretsfoundry run --script "chainlit run experiments/ui.py"
  ```

### Deploy the chatbot

  ```
   devspace deploy
  ```

## Evaluation


### RAG base evaluation dataset

The list of runs `runs.csv` has been built by getting all the runs from the beginning using:
```
export LANGCHAIN_API_KEY=<key>
cd evals/
python3 rag-evals.py save_runs --days 400
```

Then we use [lilac](https://docs.lilacml.com/) to get the most interesting questions by clustering them per topic/category. "Associations in France" was the one chosen, and we also deleted some rows due to irrelevance.

> The clustering repartition is available here: [Clustering Repartition](https://github.com/mongulu-cm/tchoung-te/pull/127#issuecomment-2174444629)

Finally, you just need to do:
```
export LANGCHAIN_API_KEY=<key>
cd evals/
python3 rag.py ragas_eval tchoung-te --run_ids_file=runs.csv
python3 rag.py deepeval tchoung-te --run_ids_file=runs.csv
```

### RAG offline evaluation


Whenever you change a parameter that can affect RAG, you can execute all inputs present in evals/base_ragas_evaluation.csv using langsmith to track them. Then you just have to get the runs and execute above command. As it's just 27 elements, you will be able to compare results manually. 

### Backtesting the prompt
  ```
   cd etl/
   python3 backtesting_prompt.py
  ```
  Create the dataset on which you want to test the new prompt on langSmith. Then run the file above to backtest and see the results of the new prompt on the dataset. You would specify in the file the name of the dataset before running



## Diagrammes des scripts
![Diagramme scripts](https://github.com/user-attachments/assets/38b926a3-a3cd-4f23-823f-1373a7409711)


## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/gttakam"><img src="https://avatars.githubusercontent.com/u/62386113?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Ghislain TAKAM</b></sub></a><br /><a href="#tutorial-gttakam" title="Tutorials">✅</a> <a href="#data-gttakam" title="Data">🔣</a></td>
    <td align="center"><a href="https://github.com/pdjiela"><img src="https://avatars.githubusercontent.com/u/36527810?v=4?s=100" width="100px;" alt=""/><br /><sub><b>pdjiela</b></sub></a><br /><a href="#tutorial-pdjiela" title="Tutorials">✅</a></td>
    <td align="center"><a href="https://github.com/DimitriTchapmi"><img src="https://avatars.githubusercontent.com/u/15048420?v=4?s=100" width="100px;" alt=""/><br /><sub><b>DimitriTchapmi</b></sub></a><br /><a href="#tutorial-DimitriTchapmi" title="Tutorials">✅</a></td>
    <td align="center"><a href="https://github.com/GNOKAM"><img src="https://avatars.githubusercontent.com/u/60141878?v=4?s=100" width="100px;" alt=""/><br /><sub><b>GNOKAM</b></sub></a><br /><a href="#tutorial-GNOKAM" title="Tutorials">✅</a> <a href="#data-GNOKAM" title="Data">🔣</a></td>
    <td align="center"><a href="https://github.com/fabiolatagne97"><img src="https://avatars.githubusercontent.com/u/60782218?v=4?s=100" width="100px;" alt=""/><br /><sub><b>fabiolatagne97</b></sub></a><br /><a href="#tutorial-fabiolatagne97" title="Tutorials">✅</a> <a href="#data-fabiolatagne97" title="Data">🔣</a></td>
    <td align="center"><a href="https://github.com/hsiebenou"><img src="https://avatars.githubusercontent.com/u/45689273?v=4?s=100" width="100px;" alt=""/><br /><sub><b>hsiebenou</b></sub></a><br /><a href="#data-hsiebenou" title="Data">🔣</a> <a href="https://github.com/mongulu-cm/tchoung-te/commits?author=hsiebenou" title="Tests">⚠️</a> <a href="#tutorial-hsiebenou" title="Tutorials">✅</a></td>
    <td align="center"><a href="http://flomint.github.io"><img src="https://avatars.githubusercontent.com/u/33840477?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Flomin TCHAWE</b></sub></a><br /><a href="https://github.com/mongulu-cm/tchoung-te/commits?author=flominT" title="Code">💻</a> <a href="#tutorial-flominT" title="Tutorials">✅</a> <a href="#data-flominT" title="Data">🔣</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/billmetangmo"><img src="https://avatars.githubusercontent.com/u/25366207?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Bill Metangmo</b></sub></a><br /><a href="https://github.com/mongulu-cm/tchoung-te/commits?author=billmetangmo" title="Code">💻</a> <a href="#data-billmetangmo" title="Data">🔣</a> <a href="#ideas-billmetangmo" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/mongulu-cm/tchoung-te/commits?author=billmetangmo" title="Tests">⚠️</a> <a href="#tutorial-billmetangmo" title="Tutorials">✅</a></td>
    <td align="center"><a href="https://github.com/dimitrilexi"><img src="https://avatars.githubusercontent.com/u/40074715?v=4?s=100" width="100px;" alt=""/><br /><sub><b>dimitrilexi</b></sub></a><br /><a href="#data-dimitrilexi" title="Data">🔣</a></td>
    <td align="center"><a href="https://github.com/ngnnpgn"><img src="https://avatars.githubusercontent.com/u/28226134?v=4?s=100" width="100px;" alt=""/><br /><sub><b>ngnnpgn</b></sub></a><br /><a href="#data-ngnnpgn" title="Data">🔣</a></td>
    <td align="center"><a href="https://github.com/Tchepga"><img src="https://avatars.githubusercontent.com/u/34720602?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Tchepga Patrick</b></sub></a><br /><a href="#data-Tchepga" title="Data">🔣</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!!
