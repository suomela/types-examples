Type and hapax accumulation curves — examples
=============================================

Sample data for https://github.com/suomela/types

For more information, see
http://users.ics.aalto.fi/suomela/types2/


Downloading and compilation
---------------------------

See https://github.com/suomela/types for more information.

    git clone git://github.com/suomela/types.git
    git clone git://github.com/suomela/types-examples.git

    cd types
    ./config
    make
    make check
    cd ..

    cd types-examples


Examples
--------

There are sample data set available in the following subdirectories:

    example1
    example2
    example3

You can experiment with the data sets as follows:

    cd example1
    bin/types-run
    bin/types-plot
    cd ..

Then open following file in your web browser:

    example1/html/index.html

The output should be similar to these pages:

  - http://users.ics.aalto.fi/suomela/types2/example1/
  - http://users.ics.aalto.fi/suomela/types2/example2/
  - http://users.ics.aalto.fi/suomela/types2/example3/

The computation will take a while, typically *several hours* unless you
are using a high-performance computing cluster. If you are impatient,
you can try the following commands that will finish in a couple of
minutes (however, the results are of a much worse quality):

    cd example1
    bin/types-run --citer=100000 --piter=100000
    bin/types-plot
    cd ..


License
-------

### Example 1

Sample data by Tanja Säily.

Derived from *CEEC*, the Corpus of Early English Correspondence:
http://www.helsinki.fi/varieng/CoRD/corpora/CEEC/

To contact the author, see
http://www.helsinki.fi/varieng/people/varieng_saily.html


### Example 2

Sample data derived from the *DBLP Computer Science Bibliography*:
http://www.informatik.uni-trier.de/~ley/db/
(source data timestamp 2012-10-29, downloaded 2012-10-30)

DBLP is Copyright (c) 1993-2011 by Michael Ley (University of Trier,
Informatik) and Schloss Dagstuhl - Leibniz-Zentrum für Informatik GmbH.

DBLP data is released under the ODC-BY 1.0 license:
http://opendatacommons.org/licenses/by/summary/


### Example 3

Sample data derived from the following Stack Exchange sites:

  - http://english.stackexchange.com/  (English Language and Usage)
  - http://math.stackexchange.com/     (Mathematics)
  - http://cstheory.stackexchange.com/ (Theoretical Computer Science)
  - http://physics.stackexchange.com/  (Physics)

The data is extracted using the StackExchange Data Explorer:
http://data.stackexchange.com/
(source data timestamp 2012-06-27, downloaded 2012-11-06)

The data is licensed under cc-wiki with attribution required:
http://creativecommons.org/licenses/by-sa/3.0/
