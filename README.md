# Movies Anywhere Downloader

Download movies from Movies Anywhere with all audio tracks and subtitles.

## Requirements

- Python 3.8+
- [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE)
- [Bento4 mp4decrypt](https://github.com/axiomatic-systems/Bento4)
- FFmpeg
- [WidevineProxy2](https://github.com/AXE-Starter/WidevineProxy2) browser extension

## Installation

```bash
git clone <REPO_URL>
cd <REPO_NAME>
pip install -e .
```

## Getting WidevineProxy2

1. Download from: https://github.com/AXE-Starter/WidevineProxy2
2. Install the browser extension in Firefox or Chrome
3. Go to extension settings and enable "Save Logs"

## Usage

1. Open Movies Anywhere in your browser with WidevineProxy2 active
2. Play the movie you want to download (let it buffer a few seconds)
3. Export logs from WidevineProxy2 (click extension icon -> Export Logs)
4. Run the downloader:

```bash
movies-anywhere ~/Downloads/logs.json "Movie Name"
```

### Examples

```bash
# Download with custom name
movies-anywhere ~/Downloads/logs.json "The Sound Of Music"

# Download with auto-generated name
movies-anywhere ~/Downloads/logs.json

# Specify output directory
movies-anywhere ~/Downloads/logs.json "Movie Name" --dir ~/Movies
```

## Output

- Downloads to `~/Downloads/Movies/[Movie Name]/`
- MKV format with all audio and subtitle tracks
- Automatically removes duplicate/broken subtitle tracks

## Troubleshooting

**"No valid entries found in logs"**
- Make sure you played the movie in your browser first
- Check that WidevineProxy2 captured the keys (look for entries in the logs.json)

**"Logs file not found"**
- Use quotes around the path if it contains special characters: `"/path/to/logs(1).json"`

---

```

                                            ==
                                          =======
                                       ===========
                                         =============         *===
                                     ================       %*+====+
                                       =============     %%#+%======
                                         ==========+++++  %%*==========
                                      =============++++    %%=========
                                       ===========+++++#####=========
                                         =========++++  ####============
                                       ==============++++###==========
                                       %============++++***=========
                                     +#%%+==========++*****============
                                      +**%#========+++=#***+=========
                                      ==*+#========+++=##***========
                               +== +++===+#%+======++==*****=======
                               ===+++++===========+*====****=====+
                             ====================+++=====##*=++++===
                            =========+++=========++========+++++=====
                              ====+===+==+====+==++=====+%%*++++======
                             =+=======+=+++==+===++======++++++======
                               ======+====*==*===++=====+++++++=======
                               +=========+*%*+==+++=====++++++======
                                 ========+*##*==+++=====++++++++++*
                                  +==++==+=*#*==+++=====++++++==++++
                                    =====***#+==+++===++++++++++++
                                      ===+#%*===++++=   +++++++++
                                      ====+%*==+=+==      ++++
                                      ====+ *==+=+==     +===
                                       ====+*==+=+==     ====
                                       ====+*==+=+=     ====
                                       ==+==#==++==    =====
                                       ==+==*==++==    ====
                                        ==*=*===+==   =====
                                        #***#======%%@====
                                        %*%%###############
                                         *=*#===+== ==+==
                                          ==%===*==#==+==
                                          *=%========++=
                                          %+*==+=+==++==
                                          %%%*+++%**####%
                                           +*########*==
                                           =**==+#==++=
                                           =++==+*=====
                                           =====++=====
                                           =====++=====
                                           ============
                                           ======+=====
                                           ======++====
                                            ==+==++====
                                            ==*==++===
                                            == == ++==
                              ____.       .__                   __
                             |    |_  _  _|  |__   ____   _____/  |_
                             |    \ \/ \/ /  |  \_/ __ \_/ __ \   __\
                         /\__|    |\     /|   Y  \  ___/\  ___/|  |
                         \________| \/\_/ |___|  /\___  >\___  >__|
                                           \/     \/     \/

```
