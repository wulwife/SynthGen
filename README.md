# SynthGen

`SynthGen` is a series of modules/objects to easen the production of synthetic seismic waveforms.
It utilizes `fomost` from the `pyrocko` package to do this.

### Install QSEIS

In order to generate synthetics, the package needs to have `qseis` installed.
To do so, follow this steps:

```bash
cd /where/to/install/parentDir
git clone https://git.gfz-potsdam.de/fomosto-backends/fomosto-qseis.git
cd fomosto-qseis
# Install `automake` if not present in your machine:
#   LINUX: sudo apt-get install automake autoconf
#   MACOS (with Xcode installed): brew install autoconf automake libtool
autoreconf -i
./configure  --prefix=./bin
make install
# Now add the bin folder to your ~/.bash_rc (Linux) or ~/.bash_profile (Mac) PATH
```
