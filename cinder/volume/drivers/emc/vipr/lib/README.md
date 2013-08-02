ViPR CLI scripts, build 1.0.0.7.541

The volume.py has been modified from the original script, as shown below, to make volume creation successful:

548c548
<              'vpool' : {'id' : vpool_uri}
---
>              'vpool' : vpool_uri

