types2: Type and hapax accumulation curves — examples
=====================================================

Sample data for https://github.com/suomela/types

For more information, see
http://users.ics.aalto.fi/suomela/types2/


Quick start
-----------

Open the following files in your web browser and explore:

    bnc-output/web/index.html
    ceec-output/web/index.html

These are also available at:

  - http://users.ics.aalto.fi/suomela/types2/bnc/
  - http://users.ics.aalto.fi/suomela/types2/ceec/


Directories
-----------

`empty`: empty database, without any input data.

`bnc-input` and `ceec-input`: input data.

`bnc-output` and `ceec-output`: end results after running the following
commands:

    types-run
    types-web


Case study: BNC and -er
-----------------------

This data set is based on the following sources:

  - British National Corpus (BNC)
  - MorphoQuantics, http://morphoquantics.co.uk

The results are linked with the BNCweb web interface (Lancaster University).
To access BNCweb, you will need a user account.

Scripts related to the construction of this data set are available at
https://github.com/suomela/bnc-affix


Case study: CEEC, -ity, and -ness
---------------------------------

The input data is in directory `bnc-input`.

Directory `bnc-output` shows the end result after running:

    types-run
    types-web

This data set is based on the following sources:

  - Corpus of Early English Correspondence (CEEC),
    http://www.helsinki.fi/varieng/CoRD/corpora/CEEC/

The results are linked with the CEECer web interface (University of Helsinki),
To access BNCweb, you will need a user account.


Running times
-------------

With default parameters, on a typical desktop computer
(Apple iMac late 2015, with a 4-core 3.2-GHz Intel Core i5):

  - BNC: approx. 6 min
  - CEEC: approx. 5 min



Acknowledgements
----------------

Data cited herein have been extracted from the British National Corpus,
distributed by the University of Oxford on behalf of the BNC Consortium.
All rights in the texts cited are reserved.


Authors
-------

  - Tanja Säily, University of Helsinki:
    http://www.helsinki.fi/varieng/people/varieng_saily.html

  - Jukka Suomela, Aalto University:
    http://users.ics.aalto.fi/suomela/
