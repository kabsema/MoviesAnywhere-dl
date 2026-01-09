# Movies Anywhere Downloader

Download movies from Movies Anywhere with all audio tracks and subtitles.

## Requirements

- Python 3.8+
- [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE)
- [Bento4 mp4decrypt](https://github.com/axiomatic-systems/Bento4)
- FFmpeg
- [WidevineProxy2](https://github.com/DevLARLEY/WidevineProxy2) browser extension

## Installation

```bash
git clone https://github.com/jwheet/MoviesAnywhere-dl
cd MoviesAnywhere-dl
pip install -e .
```

## Getting and Using WidevineProxy2

### Firefox Installation

1.  Download the `.xpi` file from the [WidevineProxy2 releases page](https://github.com/DevLARLEY/WidevineProxy2/releases).
2.  In Firefox, navigate to `about:addons`.
3.  Click the gear icon (⚙️) and select "Install Add-on From File...".
4.  Select the `.xpi` file you downloaded.
5.  Pin the extension to your toolbar for easy access.

### Chrome Installation

1.  Download the `.zip` file from the [WidevineProxy2 releases page](https.github.com/DevLARLEY/WidevineProxy2/releases).
2.  In Chrome, navigate to `chrome://extensions/`.
3.  Enable "Developer mode" using the toggle in the top right corner.
4.  Drag and drop the downloaded `.zip` file into the extensions window, or click "Load unpacked" and select the extracted zip folder.
5.  Pin the extension to your toolbar for easy access.

### Configuration and Log Export

1.  Click the WidevineProxy2 extension icon in your toolbar.
2.  In the popup, slide the toggle to enable the extension.
3.  Place your Widevine CDM (Content Decryption Module) key file (a `.wvd` file) into the 'cdm' folder of this project.
4.  Click "Choose File" and upload the `.wvd` file located in the `cdm` directory of this project.
5.  Navigate to Movies Anywhere and play the movie you want to download. Let it buffer for a few seconds.
6.  Click the extension icon again and click "Export Logs" at the bottom to download the `logs.json` file.

## Usage

Run the downloader:

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
