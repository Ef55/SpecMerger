{
  description = "Conformance Checker for Specifications";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-23.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }@input:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        devShells = {
            default = pkgs.mkShell {
              buildInputs = with pkgs; [
                python311Packages.requests
                python311Packages.beautifulsoup4
                python311Packages.hatchling
              ];
          };
        };

        packages = rec {
          spec-merger = pkgs.python3Packages.buildPythonPackage rec {
            name = "SpecMerger";
            src = ./..;
            propagatedBuildInputs = with pkgs; [
              python311
              python311Packages.hatchling
            ];
            format = "pyproject";
          };

          default = spec-merger;
        };
      });
}
