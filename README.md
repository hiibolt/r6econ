# r6econ
Consistantly monitors the R6 Marketplace based on a tracking list. 

The Discord bot tracks sales over time, also presenting extra item data not otherwise shown on the R6 Marketplace.

Much of the data this gathers can be used to manipulate the market to your advantage.

## Commands:
- ### econ list
  ![image](https://github.com/hiibolt/r6econ/assets/91273156/02ef4b4c-0965-408c-bda4-ff59da242ce2)

  Lists all tracked skins.
- ### econ name \<skin name>
  ![image](https://github.com/hiibolt/r6econ/assets/91273156/bc001157-4f17-41a1-a5fe-4ddd448e05b4)
  
  Displays the buyer, seller, and local RAP analysis.
- ### econ id \<item id>
  ![image](https://github.com/hiibolt/r6econ/assets/91273156/700c971f-da4e-4ff8-ac6f-6d3cfa04fb28)
  
  Functionally the same as the above, but allows the direct lookup by the item's static ID.
- ### econ graph <# of entries | all> <unit of time (days | hours | minutes )> <item id>
  ![image](https://github.com/hiibolt/r6econ/assets/91273156/52babf14-2e8b-44e2-98b8-661704a443bb)

## Setup (Recommended)

### Prequisites
- [python](https://www.python.org/)
- [pip](https://pypi.org/project/pip/)
  
### Windows Command Prompt
```bat
set AUTH_EMAIL=foo@example.com
set AUTH_PW=mysecretpassword
set TOKEN=as876df5as876df5as87d6f5
pip install -r requirements.txt
python3.exe server.py
```

### PowerShell
```ps1
$env:UTH_EMAIL=foo@example.com
$env:AUTH_PW=mysecretpassword
$env:TOKEN=as876df5as876df5as87d6f5
pip install -r requirements.txt
python3.exe server.py
```

### Bash
```sh
export AUTH_EMAIL=foo@example.com
export AUTH_PW=mysecretpassword
export TOKEN=as876df5as876df5as87d6f5
pip install -r requirements.txt
python3 server.py
```


## Setup (Nix) (Not Recommended for Beginners)

### Prerequisites

- [nix](https://nixos.org/)
- [nix flakes](https://nixos.wiki/wiki/Flakes)

### Instructions

Set the following environment variables:
- AUTH_EMAIL: Your Ubisoft email.
- AUTH_PW: Your associated Ubisoft password.
- TOKEN: The run token for your Discord bot.

With flake functionality enabled, run `nix develop`.

Then, run `python server.py`.


## Credits
Much of the authentication code was sourced from https://github.com/CNDRD/siegeapi. 

Thank you for the well-documented code! <3
