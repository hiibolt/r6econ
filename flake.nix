{
  description = "Development environment for Python";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };
  outputs = { self, nixpkgs }: 
    let
      system = "x86_64-linux";
      
      pkgs = import nixpkgs { 
        inherit system;
      };

      python-package-list = p: with p; [
        pip
      ];
      python = pkgs.python310.withPackages python-package-list;
    in
    {
    devShells.x86_64-linux.default = pkgs.mkShell {
      buildInputs = [ python ];
      shellHook = 
        ''
        python -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [
          pkgs.stdenv.cc.cc
        ]}
        '';
      
    };
  };
}