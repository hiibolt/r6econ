# r6econ
Consistantly monitors the R6 Marketplace based on a tracking list. 

The Discord bot tracks sales over time, also presenting extra item data not otherwise shown on the R6 Marketplace.

Much of the data this gathers can be used to manipulate the market to your advantage.



## Setup (Recommended)

### Prequisites
- [python](https://www.python.org/)
- [pip](https://pypi.org/project/pip/)
- [A discord bot and its token](https://www.writebots.com/discord-bot-token/)
  
First, clone the repo and add a 'data.json' file to /assets, and leave the contents as ```{}```

Next, add an 'ids.json' file to /assets, and place any items and their item IDs in the contents. There is an starting example in the assets folder of this repo.

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
$env:AUTH_EMAIL="foo@example.com"
$env:AUTH_PW="mysecretpassword"
$env:TOKEN="as876df5as876df5as87d6f5"
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

## Setup (Docker Compose)
Be sure to bind a volume for your assets and add a `data.json` file with contents `{}`, as well as an `ids.json` file (template `ids.json` can be found in this repository).

`compose.yml`
```yml
services:
  r6econ-bot:
    image: ghcr.io/hiibolt/r6econ:latest
    volumes:
      - 'assets:/app/assets'
    environment:
      - AUTH_EMAIL=<your ubisoft email here>
      - AUTH_PW=<your ubisoft password here>
      - TOKEN=<your discord token here>
volumes:
  assets:

```


## Setup (Nix) (Not Recommended for Beginners)

### Prerequisites

- [nix](https://nixos.org/)
- [nix flakes](https://nixos.wiki/wiki/Flakes)
- [A discord bot and its token](https://www.writebots.com/discord-bot-token/)

First, clone the repo and add a 'data.json' file to /assets, and leave the contents as ```{}```


### Instructions

Set the following environment variables:
- AUTH_EMAIL: Your Ubisoft email.
- AUTH_PW: Your associated Ubisoft password.
- TOKEN: The run token for your Discord bot.

With flake functionality enabled, run `nix develop`.

Then, run `python server.py`.


## Commands:
- ### econ list
  Lists all available names you can search for. It's recommended that you use item IDs instead, however.
  
  ![image](https://github.com/hiibolt/r6econ/assets/91273156/02ef4b4c-0965-408c-bda4-ff59da242ce2)

  Lists all tracked skins.
- ### econ name \<skin name>
  Fetches the economical trends of an item based on its name in `ids.json`.
  
  ![image](https://github.com/hiibolt/r6econ/assets/91273156/bc001157-4f17-41a1-a5fe-4ddd448e05b4)
  
- ### econ id \<item id>
  Functionally the same as the above, but allows the direct lookup by the item's static ID.

  ![image](https://github.com/hiibolt/r6econ/assets/91273156/700c971f-da4e-4ff8-ac6f-6d3cfa04fb28)
  
- ### econ graph <# of entries | all> <unit of time (days | hours | minutes )> <item id>
  Displays a graph of the current state of an item.

  This is the most useful command, and can be used to determine when to buy or sell. A basic example of how to make informed decisions is in the linked article in the description of this repo.

  ![image](https://github.com/hiibolt/r6econ/assets/91273156/52babf14-2e8b-44e2-98b8-661704a443bb)

- ### econ profit \<$ purchased for> \<item id>
  Calculates how much you need to sell for to gain profit, and estimates your profit if sold right now (according to the RAP 10x).

  ![image](https://github.com/hiibolt/r6econ/assets/91273156/75304082-df33-446d-9f7f-6f9c0cffc573)


- ### econ help
 Default message that is shown when an invalid command is used or the user runs `econ help`.
  
  ![image](https://github.com/hiibolt/r6econ/assets/91273156/76efecb4-114d-4212-850b-1d6ff3825b47)


## Credits
Much of the authentication code was sourced from https://github.com/CNDRD/siegeapi. 

Thank you for the well-documented code! <3
