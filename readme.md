In the game Dungeons and Dragons Online (DDO), you can build your very own character. Use Maetrims builder to plan your build: https://github.com/Maetrim/DDOBuilderV2

## Optimize your build
But how do you know if what you build is better than the last version? These scripts are a proposal to calculate fitness scores for your builds. When you change something in the build, check the new fitness scores to see if your new version is better than it used to be. Disclaimer: this is prototype code to enable discussion on the math. It's not going to work on all build exports of Maetrim's DDOBuilderV2.

## How to run the code and import your own builds
Clone or download the code and make sure you have Python installed on your system.

### Windows
Open Windows PowerShell or the Terminal and use these commands:

```bash
cd path/to/ddobuilder-comparer/
python -m venv .venv
./.venv/Scripts/activate
pip install -r requirements.txt
```

Open the project directory in Visual Studio Code. Open `read_a_DDOBuilder_file.ipynb`, this is a Jupyter notebook. You'll find a 'Run All' button. Use it and check the `ddobuilder-comparer.log` file. You'll find two fitness scores there: an offensive one and a defensive one. The defensive fitness score should be in the same ballpark as the 'Effective hit points' score in DDO.

To test your own build file, export it in Maetrims DDOBuilderV2. Paste the code in `paste_your_export_here.txt` and run the notebook again.

## What is 'better'?
The proposal is to show one or more fitness scores in DDOBuilderV2. A good spot would be in the `Builds` pane. This way, people can compare more builds and see if the next one is going to be better.

### A first idea for an offensive fitness score
Included is a sample build for a melee character. A offensive fitness score could be:
* Calculate the average damage your character does with one normal melee hit and factor in critical hits.
* Calculate what effect melee power, doublestrike and helpless damage will have on this average hit. This gives a feeling how effective a melee attack would be if you take these stats in account. Check the code in `read_a_DDOBuilder_file.ipynb` and `ddo_stats.py` for details.

```python
offensive_fitness_score = (expected_damage *
                            stats.convert_to_factor(melee_power) * 
                            stats.convert_to_factor(doublestrike) * 
                            stats.convert_to_factor(helpless_damage_bonus))
```

### A possible defensive fitness score
In DDO, players can check their 'Effective hit points', an intuitive number that says something about how sturdy your character is. This fitness score is an approximation. The 'Effective hit points' number probably uses more stats.

```python
defensive_fitness_score = (hit_points * 
                           (1.0 + prr_percentage) *
                           (1.0 + mrr_percentage) *
                           (1.0 + stats.normalize_dodge(dodge)) *
                           (1.0 + stats.normalize_armor_class(armor_class)))
```