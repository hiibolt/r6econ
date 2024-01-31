# r6econ
Consistantly monitors the R6 Marketplace based on a tracking list. 

The Discord bot tracks sales over time, also presenting extra item data not otherwise shown on the R6 Marketplace.

Much of the data this gathers can be used to manipulate the market to your advantage.

## Commands:
- ### econ list
  ![image](https://github.com/hiibolt/r6econ/assets/91273156/02ef4b4c-0965-408c-bda4-ff59da242ce2)

  Lists all tracked skins.
- ### econ \<skin name>
  ![image](https://github.com/hiibolt/r6econ/assets/91273156/219aea7b-268c-4513-a3fc-74365a97feec)
  
  Displays the buyer, seller, and local RAP analysis.
- ### econ id \<item id>
  ![image](https://github.com/hiibolt/r6econ/assets/91273156/21639c94-7ae8-4d23-92b4-da703962a1e3)
  
  Functionally the same as the above, but allows the direct lookup by the item's static ID.

## Setup (Nix) (Recommended)

### Prerequisites

- [nix](https://nixos.org/)
- [nix flakes](https://nixos.wiki/wiki/Flakes)

### Instructions

With flake functionality enabled, run `nix develop`.

Then, run `python server.py`.

Finally, set the following environment variables:
- AUTH_EMAIL: Your Ubisoft email.
- AUTH_PW: Your associated Ubisoft password.
- TOKEN: The run token for your Discord bot.

## Setup (Basic)

### Prequisites
- [python](https://www.python.org/)
- [pip](https://pypi.org/project/pip/)

Download required packages with `pip install -r requirements.txt`.

Then, run `python server.py`.

Finally, set the following environment variables:
- AUTH_EMAIL: Your Ubisoft email.
- AUTH_PW: Your associated Ubisoft password.
- TOKEN: The run token for your Discord bot.

## Credits
Much of the authentication code was sourced from https://github.com/CNDRD/siegeapi. 

Thank you for the well-documented code! <3
