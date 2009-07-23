# Copyright 2009 by Peter Cock.  All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
#
# This module is for reading and writing FASTQ and QUAL format files as
# SeqRecord objects, and is expected to be used via the Bio.SeqIO API.

"""Bio.SeqIO support for the FASTQ and QUAL file formats.

Note that you are expected to use this code via the Bio.SeqIO interface, as
shown below.

The FASTQ file format is used frequently at the Wellcome Trust Sanger Institute
to bundle a FASTA sequence and its PHRED quality data (integers between 0 and
90).  Rather than using a single FASTQ file, often paired FASTA and QUAL files
are used containing the sequence and the quality information separately.

The PHRED software reads DNA sequencing trace files, calls bases, and
assigns a quality value between 0 and 93 (at least, 93 is the upper bound
according to the maq tool's documentation) to each called base using a logged
transformation of the error probability, Q = -10 log10( Pe ), for example::

    Pe = 1.0,         Q =  0
    Pe = 0.1,         Q = 10
    Pe = 0.01,        Q = 20
    ...
    Pe = 0.00000001,  Q = 80
    Pe = 0.000000001, Q = 90

In the QUAL format these quality values are held as space separated text in
a FASTA like file format.  In the FASTQ format, each quality values is encoded
with a single ASCI character using chr(Q+33), meaning zero maps to the
character "!" and for example 80 maps to "q".  The sequences and quality are
then stored in pairs in a FASTA like format.

Unfortunately there is no official document describing the FASTQ file format,
and worse, several related but different variants exist.  Reasonable
documentation exists at: http://maq.sourceforge.net/fastq.shtml

The good news is that Roche 454 sequencers can output files in the QUAL format,
and sensibly they use PHREP style scores like Sanger.  Converting a pair of
FASTA and QUAL files into a Sanger style FASTQ file is easy. To extract QUAL
files from a Roche 454 SFF binary file, use the Roche off instrument command
line tool "sffinfo" with the -q or -qual argument.  You can extract a matching
FASTA file using the -s or -seq argument instead.

The bad news is that Solexa/Illumina did things differently - they have their
own scoring system AND their own incompatible versions of the FASTQ format.
Solexa/Illumina quality scores use Q = - 10 log10 ( Pe / (1-Pe) ), which can
be negative.  PHRED scores and Solexa scores are NOT interchangeable (but a
reasonable mapping can be achieved between them, and they are approximately
equal for high quality reads).

Confusingly early Solexa pipelines produced a FASTQ like file but using their
own score mapping and an ASCII offset of 64. To make things worse, for the
Solexa/Illumina pipeline 1.3 onwards, they introduced a third variant of the
FASTQ file format, this time using PHRED scores (which is more consistent) but
with an ASCII offset of 64.

i.e. There are at least THREE different and INCOMPATIBLE variants of the FASTQ
file format: The original Sanger PHRED standard, and two from Solexa/Illumina.

You are expected to use this module via the Bio.SeqIO functions, with the
following format names:

 - "qual" means simple quality files using PHRED scores (e.g. from Roche 454)
 - "fastq" means Sanger style FASTQ files using PHRED scores and an ASCII
    offset of 33 (e.g. from the NCBI Short Read Archive).
 - "fastq-solexa" means old Solexa (and also very early Illumina) style FASTQ
    files, using Solexa scores with an ASCII offset 64.
 - "fastq-illumina" means new Illumina 1.3+ style FASTQ files, using PHRED
    scores but with an ASCII offset 64.

We could potentially add support for "qual-solexa" meaning QUAL files which
contain Solexa scores, but thus far there isn't any reason to use such files.

For example, consider the following short FASTQ file::

    @EAS54_6_R1_2_1_413_324
    CCCTTCTTGTCTTCAGCGTTTCTCC
    +
    ;;3;;;;;;;;;;;;7;;;;;;;88
    @EAS54_6_R1_2_1_540_792
    TTGGCAGGCCAAGGCCGATGGATCA
    +
    ;;;;;;;;;;;7;;;;;-;;;3;83
    @EAS54_6_R1_2_1_443_348
    GTTGCTTCTGGCGTGGGTGGGGGGG
    +
    ;;;;;;;;;;;9;7;;.7;393333

This contains three reads of length 25.  From the read length these were
probably originally from an early Solexa/Illumina sequencer but this file
follows the Sanger FASTQ convention (PHRED style qualities with an ASCII
offet of 33).  This means we can parse this file using Bio.SeqIO using
"fastq" as the format name:

    >>> from Bio import SeqIO
    >>> for record in SeqIO.parse(open("Quality/example.fastq"), "fastq") :
    ...     print record.id, record.seq
    EAS54_6_R1_2_1_413_324 CCCTTCTTGTCTTCAGCGTTTCTCC
    EAS54_6_R1_2_1_540_792 TTGGCAGGCCAAGGCCGATGGATCA
    EAS54_6_R1_2_1_443_348 GTTGCTTCTGGCGTGGGTGGGGGGG

The qualities are held as a list of integers in each record's annotation:

    >>> print record
    ID: EAS54_6_R1_2_1_443_348
    Name: EAS54_6_R1_2_1_443_348
    Description: EAS54_6_R1_2_1_443_348
    Number of features: 0
    Per letter annotation for: phred_quality
    Seq('GTTGCTTCTGGCGTGGGTGGGGGGG', SingleLetterAlphabet())
    >>> print record.letter_annotations["phred_quality"]
    [26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 24, 26, 22, 26, 26, 13, 22, 26, 18, 24, 18, 18, 18, 18]

You can use the SeqRecord format method to show this in the QUAL format:

    >>> print record.format("qual")
    >EAS54_6_R1_2_1_443_348
    26 26 26 26 26 26 26 26 26 26 26 24 26 22 26 26 13 22 26 18
    24 18 18 18 18
    <BLANKLINE>

Or go back to the FASTQ format,

    >>> print record.format("fastq")
    @EAS54_6_R1_2_1_443_348
    GTTGCTTCTGGCGTGGGTGGGGGGG
    +
    ;;;;;;;;;;;9;7;;.7;393333
    <BLANKLINE>

Or, using the Illumina 1.3+ FASTQ encoding (PHRED values with an ASCII offset
of 64):

    >>> print record.format("fastq-illumina")
    @EAS54_6_R1_2_1_443_348
    GTTGCTTCTGGCGTGGGTGGGGGGG
    +
    ZZZZZZZZZZZXZVZZMVZRXRRRR
    <BLANKLINE>

You can also get Biopython to convert the scores and show a Solexa style
FASTQ file:

    >>> print record.format("fastq-solexa")
    @EAS54_6_R1_2_1_443_348
    GTTGCTTCTGGCGTGGGTGGGGGGG
    +
    ZZZZZZZZZZZXZVZZMVZRXRRRR
    <BLANKLINE>

Notice that this is actually the same output as above using "fastq-illumina"
as the format! The reason for this is all these scores are high enough that
the PHRED and Solexa scores are almost equal. The differences become apparent
for poor quality reads. See the functions solexa_quality_from_phred and
phred_quality_from_solexa for more details.
 
If you wanted to trim your sequences (perhaps to remove low quality regions,
or to remove a primer sequence), try slicing the SeqRecord objects.  e.g.

    >>> sub_rec = record[5:15]
    >>> print sub_rec
    ID: EAS54_6_R1_2_1_443_348
    Name: EAS54_6_R1_2_1_443_348
    Description: EAS54_6_R1_2_1_443_348
    Number of features: 0
    Per letter annotation for: phred_quality
    Seq('TTCTGGCGTG', SingleLetterAlphabet())
    >>> print sub_rec.letter_annotations["phred_quality"]
    [26, 26, 26, 26, 26, 26, 24, 26, 22, 26]
    >>> print sub_rec.format("fastq")
    @EAS54_6_R1_2_1_443_348
    TTCTGGCGTG
    +
    ;;;;;;9;7;
    <BLANKLINE>
    
If you wanted to, you could read in this FASTQ file, and save it as a QUAL file:

    >>> from Bio import SeqIO
    >>> record_iterator = SeqIO.parse(open("Quality/example.fastq"), "fastq")
    >>> out_handle = open("Quality/temp.qual", "w")
    >>> SeqIO.write(record_iterator, out_handle, "qual")
    3
    >>> out_handle.close()

You can of course read in a QUAL file, such as the one we just created:

    >>> from Bio import SeqIO
    >>> for record in SeqIO.parse(open("Quality/temp.qual"), "qual") :
    ...     print record.id, record.seq
    EAS54_6_R1_2_1_413_324 ?????????????????????????
    EAS54_6_R1_2_1_540_792 ?????????????????????????
    EAS54_6_R1_2_1_443_348 ?????????????????????????

Notice that QUAL files don't have a proper sequence present!  But the quality
information is there:

    >>> print record
    ID: EAS54_6_R1_2_1_443_348
    Name: EAS54_6_R1_2_1_443_348
    Description: EAS54_6_R1_2_1_443_348
    Number of features: 0
    Per letter annotation for: phred_quality
    UnknownSeq(25, alphabet = SingleLetterAlphabet(), character = '?')
    >>> print record.letter_annotations["phred_quality"]
    [26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 24, 26, 22, 26, 26, 13, 22, 26, 18, 24, 18, 18, 18, 18]

Just to keep things tidy, if you are following this example yourself, you can
delete this temporary file now:

    >>> import os
    >>> os.remove("Quality/temp.qual")

Sometimes you won't have a FASTQ file, but rather just a pair of FASTA and QUAL
files.  Because the Bio.SeqIO system is designed for reading single files, you
would have to read the two in separately and then combine the data.  However,
since this is such a common thing to want to do, there is a helper iterator
defined in this module that does this for you - PairedFastaQualIterator.

Alternatively, if you have enough RAM to hold all the records in memory at once,
then a simple dictionary approach would work:

    >>> from Bio import SeqIO
    >>> reads = SeqIO.to_dict(SeqIO.parse(open("Quality/example.fasta"), "fasta"))
    >>> for rec in SeqIO.parse(open("Quality/example.qual"), "qual") :
    ...     reads[rec.id].letter_annotations["phred_quality"]=rec.letter_annotations["phred_quality"]

You can then access any record by its key, and get both the sequence and the
quality scores.

    >>> print reads["EAS54_6_R1_2_1_540_792"].format("fastq")
    @EAS54_6_R1_2_1_540_792
    TTGGCAGGCCAAGGCCGATGGATCA
    +
    ;;;;;;;;;;;7;;;;;-;;;3;83
    <BLANKLINE>

It is important that you explicitly tell Bio.SeqIO which FASTQ variant you are
using ("fastq" for the Sanger standard using PHRED values, "fastq-solexa" for
the original Solexa/Illumina variant, or "fastq-illumina" for the more recent
variant), as this cannot be detected reliably automatically.

To illustrate this problem, let's consider an artifical example:

    >>> from Bio.Seq import Seq
    >>> from Bio.Alphabet import generic_dna
    >>> from Bio.SeqRecord import SeqRecord
    >>> test = SeqRecord(Seq("NACGTACGTA", generic_dna), id="Test",
    ... description="Made up!")
    >>> print test.format("fasta")
    >Test Made up!
    NACGTACGTA
    <BLANKLINE>
    >>> print test.format("fastq")
    Traceback (most recent call last):
     ...
    ValueError: No suitable quality scores found in letter_annotations of SeqRecord (id=Test).

We created a sample SeqRecord, and can show it in FASTA format - but for QUAL
or FASTQ format we need to provide some quality scores. These are held as a
list of integers (one for each base) in the letter_annotations dictionary:

    >>> test.letter_annotations["phred_quality"] = [0,1,2,3,4,5,10,20,30,40]
    >>> print test.format("qual")
    >Test Made up!
    0 1 2 3 4 5 10 20 30 40
    <BLANKLINE>
    >>> print test.format("fastq")
    @Test Made up!
    NACGTACGTA
    +
    !"#$%&+5?I
    <BLANKLINE>

We can check this FASTQ encoding - the first PHRED quality was zero, and this
mapped to a exclamation mark, while the final score was 40 and this mapped to
the letter "I":

    >>> ord('!') - 33
    0
    >>> ord('I') - 33
    40
    >>> [ord(letter)-33 for letter in '!"#$%&+5?I']
    [0, 1, 2, 3, 4, 5, 10, 20, 30, 40]

Similarly, we could produce an Illumina 1.3+ style FASTQ file using PHRED
scores with an offset of 64:

    >>> print test.format("fastq-illumina")
    @Test Made up!
    NACGTACGTA
    +
    @ABCDEJT^h
    <BLANKLINE>

And we can check this too - the first PHRED score was zero, and this mapped to
"@", while the final score was 40 and this mapped to "h":

    >>> ord("@") - 64
    0
    >>> ord("h") - 64
    40
    >>> [ord(letter)-64 for letter in "@ABCDEJT^h"]
    [0, 1, 2, 3, 4, 5, 10, 20, 30, 40]

Notice how different the standard Sanger FASTQ and the Illumina 1.3+ style
FASTQ files look for the same data! Then we have the older Solexa/Illumina
format to consider which encodes Solexa scores instead of PHRED scores.

First let's see what Biopython says if we convert the PHRED scores into Solexa
scores (rounding to one decimal place):

    >>> for q in [0,1,2,3,4,5,10,20,30,40] :
    ...     print "PHRED %i maps to Solexa %0.1f" % (q, solexa_quality_from_phred(q))
    PHRED 0 maps to Solexa -5.0
    PHRED 1 maps to Solexa -5.0
    PHRED 2 maps to Solexa -2.3
    PHRED 3 maps to Solexa -0.0
    PHRED 4 maps to Solexa 1.8
    PHRED 5 maps to Solexa 3.3
    PHRED 10 maps to Solexa 9.5
    PHRED 20 maps to Solexa 20.0
    PHRED 30 maps to Solexa 30.0
    PHRED 40 maps to Solexa 40.0

Now here is the record using the old Solexa style FASTQ file:

    >>> print test.format("fastq-solexa")
    @Test Made up!
    NACGTACGTA
    +
    ;;>@BCJT^h
    <BLANKLINE>

Again, this is using an ASCII offset of 64, so we can check the Solexa scores:

    >>> [ord(letter)-64 for letter in ";;>@BCJT^h"]
    [-5, -5, -2, 0, 2, 3, 10, 20, 30, 40]

This explains why the last few letters of this FASTQ output matched that using
the Illumina 1.3+ format - high quality PHRED scores and Solexa scores are
approximately equal.

"""
__docformat__ = "epytext en" #Don't just use plain text in epydoc API pages!

#See also http://blog.malde.org/index.php/2008/09/09/the-fastq-file-format-for-sequences/

from Bio.Alphabet import single_letter_alphabet
from Bio.Seq import Seq, UnknownSeq
from Bio.SeqRecord import SeqRecord
from Interfaces import SequentialSequenceWriter
from math import log

# define score offsets. See discussion for differences between Sanger and
# Solexa offsets.
SANGER_SCORE_OFFSET = 33
SOLEXA_SCORE_OFFSET = 64

def solexa_quality_from_phred(phred_quality) :
    """Covert a PHRED quality (range 0 to about 90) to a Solexa quality.

    PHRED and Solexa quality scores are both log transformations of a
    probality of error (high score = low probability of error). This function
    takes a PHRED score, transforms it back to a probability of error, and
    then re-expresses it as a Solexa score. This assumes the error estimates
    are equivalent.

    How does this work exactly? Well the PHRED quality is minus ten times the
    base ten logarithm of the probability of error::
    
     phred_quality = -10*log(error,10)

    Therefore, turning this round::

     error = 10 ** (- phred_quality / 10)
    
    Now, Solexa qualities use a different log transformation::

     solexa_quality = -10*log(error/(1-error),10)

    After substitution and a little manipulation we get::

      solexa_quality = 10*log(10**(phred_quality/10.0) - 1, 10)

    However, real Solexa files use a minimum quality of -5. This does have a
    good reason - a random a random base call would be correct 25% of the time,
    and thus have a probability of error of 0.75, which gives 1.25 as the PHRED
    quality, or -4.77 as the Solexa quality. Thus (after rounding), a random
    nucleotide read would have a PHRED quality of 1, or a Solexa quality of -5.

    Taken literally, this logarithic formula would map a PHRED quality of zero
    to a Solexa quality of minus infinity. Of course, taken literally, a PHRED
    score of zero means a probability of error of one (i.e. the base call is
    definitely wrong), which is worse than random! In practice, a PHRED quality
    of zero usually means a default value, or perhaps random - and therefore
    mapping it to the minimum Solexa score of -5 is reasonable.

    In conclusion, we follow EMBOSS, and take this logarithmic formula but also
    apply a minimum value of -5.0 for the Solexa quality, and also map a PHRED
    quality of zero to -5.0 as well.

    Note this function will return a floating point number, it is up to you to
    round this to the nearest integer if appropriate.  e.g.

    >>> print "%0.2f" % round(solexa_quality_from_phred(80),2)
    80.00
    >>> print "%0.2f" % round(solexa_quality_from_phred(50),2)
    50.00
    >>> print "%0.2f" % round(solexa_quality_from_phred(20),2)
    19.96
    >>> print "%0.2f" % round(solexa_quality_from_phred(10),2)
    9.54
    >>> print "%0.2f" % round(solexa_quality_from_phred(5),2)
    3.35
    >>> print "%0.2f" % round(solexa_quality_from_phred(4),2)
    1.80
    >>> print "%0.2f" % round(solexa_quality_from_phred(3),2)
    -0.02
    >>> print "%0.2f" % round(solexa_quality_from_phred(2),2)
    -2.33
    >>> print "%0.2f" % round(solexa_quality_from_phred(1),2)
    -5.00
    >>> print "%0.2f" % round(solexa_quality_from_phred(0),2)
    -5.00

    Notice that for high quality reads PHRED and Solexa scores are numerically
    equal. The differences are important for poor quality reads, where PHRED
    has a minimum of zero but Solexa scores can be negative.

    Finally, as a special case where None is used for a "missing value", None
    is returned:

    >>> print solexa_quality_from_phred(None)
    None
    """
    if phred_quality > 0 :
        #Solexa uses a minimum value of -5, which after rounding matches a
        #random nucleotide base call.
        return max(-5.0, 10*log(10**(phred_quality/10.0) - 1, 10))
    elif phred_quality == 0 :
        #Special case, map to -5 as discussed in the docstring
        return -5.0
    elif phred_quality is None :
        #Assume None is used as some kind of NULL or NA value; return None
        #e.g. Bio.SeqIO gives Ace contig gaps a quality of None.
        return None
    else :
        raise ValueError("PHRED qualities must be positive (or zero)")

def phred_quality_from_solexa(solexa_quality) :
    """Convert a Solexa quality (which can be negative) to a PHRED quality.

    PHRED and Solexa quality scores are both log transformations of a
    probality of error (high score = low probability of error). This function
    takes a Solexa score, transforms it back to a probability of error, and
    then re-expresses it as a PHRED score. This assumes the error estimates
    are equivalent.

    The underlying formulas are given in the documentation for the sister
    function solexa_quality_from_phred, in this case the operation is::
    
     phred_quality = 10*log(10**(solexa_quality/10.0) + 1, 10)

    This will return a floating point number, it is up to you to round this to
    the nearest integer if appropriate.  e.g.

    >>> print "%0.2f" % round(phred_quality_from_solexa(80),2)
    80.00
    >>> print "%0.2f" % round(phred_quality_from_solexa(20),2)
    20.04
    >>> print "%0.2f" % round(phred_quality_from_solexa(10),2)
    10.41
    >>> print "%0.2f" % round(phred_quality_from_solexa(0),2)
    3.01
    >>> print "%0.2f" % round(phred_quality_from_solexa(-5),2)
    1.19

    Note that a solexa_quality less then -5 is not expected, will trigger a
    warning, but will still be converted as per the logarithmic mapping
    (giving a number between 0 and 1.19 back).

    As a special case where None is used for a "missing value", None is
    returned:

    >>> print phred_quality_from_solexa(None)
    None

    """
    if solexa_quality is None :
        #Assume None is used as some kind of NULL or NA value; return None
        return None
    if solexa_quality < -5 :
        import warnings
        warnings.warn("Solexa quality less than -5 passed")
    return 10*log(10**(solexa_quality/10.0) + 1, 10)

def _get_phred_quality(record) :
    """Extract PHRED qualities from a SeqRecord's letter_annotations (PRIVATE).

    If there are no PHRED qualities, but there are Solexa qualities, those are
    used instead after conversion.
    """
    try :
        return record.letter_annotations["phred_quality"]
    except KeyError :
        pass
    try :
        return [phred_quality_from_solexa(q) for \
                q in record.letter_annotations["solexa_quality"]]
    except KeyError :
        raise ValueError("No suitable quality scores found in "
                         "letter_annotations of SeqRecord (id=%s)." \
                         % record.id)

def _get_solexa_quality(record) :
    """Extract Solexa qualities from a SeqRecord's letter_annotations (PRIVATE).

    If there are no Solexa qualities, but there are PHRED qualities, those are
    used instead after conversion.
    """
    try :
        return record.letter_annotations["solexa_quality"]
    except KeyError :
        pass
    try :
        return [solexa_quality_from_phred(q) for \
                q in record.letter_annotations["phred_quality"]]
    except KeyError :
        raise ValueError("No suitable quality scores found in "
                         "letter_annotations of SeqRecord (id=%s)." \
                         % record.id)


#TODO - Default to nucleotide or even DNA?
def FastqGeneralIterator(handle) :
    """Iterate over Fastq records as string tuples (not as SeqRecord objects).

    This code does not try to interpret the quality string numerically.  It
    just returns tuples of the title, sequence and quality as strings.  For
    the sequence and quality, any whitespace (such as new lines) is removed.

    Our SeqRecord based FASTQ iterators call this function internally, and then
    turn the strings into a SeqRecord objects, mapping the quality string into
    a list of numerical scores.  If you want to do a custom quality mapping,
    then you might consider calling this function directly.

    For parsing FASTQ files, the title string from the "@" line at the start
    of each record can optionally be omitted on the "+" lines.  If it is
    repeated, it must be identical.

    The sequence string and the quality string can optionally be split over
    multiple lines, although several sources discourage this.  In comparison,
    for the FASTA file format line breaks between 60 and 80 characters are
    the norm.

    WARNING - Because the "@" character can appear in the quality string,
    this can cause problems as this is also the marker for the start of
    a new sequence.  In fact, the "+" sign can also appear as well.  Some
    sources recommended having no line breaks in the  quality to avoid this,
    but even that is not enough, consider this example::

        @071113_EAS56_0053:1:1:998:236
        TTTCTTGCCCCCATAGACTGAGACCTTCCCTAAATA
        +071113_EAS56_0053:1:1:998:236
        IIIIIIIIIIIIIIIIIIIIIIIIIIIIICII+III
        @071113_EAS56_0053:1:1:182:712
        ACCCAGCTAATTTTTGTATTTTTGTTAGAGACAGTG
        +
        @IIIIIIIIIIIIIIICDIIIII<%<6&-*).(*%+
        @071113_EAS56_0053:1:1:153:10
        TGTTCTGAAGGAAGGTGTGCGTGCGTGTGTGTGTGT
        +
        IIIIIIIIIIIICIIGIIIII>IAIIIE65I=II:6
        @071113_EAS56_0053:1:3:990:501
        TGGGAGGTTTTATGTGGA
        AAGCAGCAATGTACAAGA
        +
        IIIIIII.IIIIII1@44
        @-7.%<&+/$/%4(++(%

    This is four PHRED encoded FASTQ entries originally from an NCBI source
    (given the read length of 36, these are probably Solexa Illumna reads where
    the quality has been mapped onto the PHRED values).

    This example has been edited to illustrate some of the nasty things allowed
    in the FASTQ format.  Firstly, on the "+" lines most but not all of the
    (redundant) identifiers are ommited.  In real files it is likely that all or
    none of these extra identifiers will be present.

    Secondly, while the first three sequences have been shown without line
    breaks, the last has been split over multiple lines.  In real files any line
    breaks are likely to be consistent.

    Thirdly, some of the quality string lines start with an "@" character.  For
    the second record this is unavoidable.  However for the fourth sequence this
    only happens because its quality string is split over two lines.  A naive
    parser could wrongly treat any line starting with an "@" as the beginning of
    a new sequence!  This code copes with this possible ambiguity by keeping
    track of the length of the sequence which gives the expected length of the
    quality string.

    Using this tricky example file as input, this short bit of code demonstrates
    what this parsing function would return:

    >>> handle = open("Quality/tricky.fastq", "rU")
    >>> for (title, sequence, quality) in FastqGeneralIterator(handle) :
    ...     print title
    ...     print sequence, quality
    071113_EAS56_0053:1:1:998:236
    TTTCTTGCCCCCATAGACTGAGACCTTCCCTAAATA IIIIIIIIIIIIIIIIIIIIIIIIIIIIICII+III
    071113_EAS56_0053:1:1:182:712
    ACCCAGCTAATTTTTGTATTTTTGTTAGAGACAGTG @IIIIIIIIIIIIIIICDIIIII<%<6&-*).(*%+
    071113_EAS56_0053:1:1:153:10
    TGTTCTGAAGGAAGGTGTGCGTGCGTGTGTGTGTGT IIIIIIIIIIIICIIGIIIII>IAIIIE65I=II:6
    071113_EAS56_0053:1:3:990:501
    TGGGAGGTTTTATGTGGAAAGCAGCAATGTACAAGA IIIIIII.IIIIII1@44@-7.%<&+/$/%4(++(%
    >>> handle.close()

    Finally we note that some sources state that the quality string should
    start with "!" (which using the PHRED mapping means the first letter always
    has a quality score of zero).  This rather restrictive rule is not widely
    observed, so is therefore ignored here.  One plus point about this "!" rule
    is that (provided there are no line breaks in the quality sequence) it
    would prevent the above problem with the "@" character.
    """
    #Skip any text before the first record (e.g. blank lines, comments?)
    while True :
        line = handle.readline()
        if line == "" : return #Premature end of file, or just empty?
        if line[0] == "@" :
            break

    while True :
        if line[0]!="@" :
            raise ValueError("Records in Fastq files should start with '@' character")
        title_line = line[1:].rstrip()
        #Will now be at least one line of quality data - in most FASTQ files
        #just one line! We therefore use string concatenation (if needed)
        #rather using than the "".join(...) trick just in case it is multiline:
        seq_string = handle.readline().rstrip()
        #There may now be more sequence lines, or the "+" quality marker line:
        while True:
            line = handle.readline()
            if not line :
                raise ValueError("End of file without quality information.")
            if line[0] == "+":
                #The title here is optional, but if present must match!
                second_title = line[1:].rstrip()
                if second_title and second_title != title_line :
                    raise ValueError("Sequence and quality captions differ.")
                break
            seq_string += line.rstrip() #removes trailing newlines
        seq_len = len(seq_string)

        #Will now be at least one line of quality data...
        quality_string = handle.readline().strip()
        #There may now be more quality data, or another sequence, or EOF
        while True:
            line = handle.readline()
            if not line : break #end of file
            if line[0] == "@":
                #This COULD be the start of a new sequence. However, it MAY just
                #be a line of quality data which starts with a "@" character.  We
                #should be able to check this by looking at the sequence length
                #and the amount of quality data found so far.
                if len(quality_string) >= seq_len :
                    #We expect it to be equal if this is the start of a new record.
                    #If the quality data is longer, we'll raise an error below.
                    break
                #Continue - its just some (more) quality data.
            quality_string += line.rstrip()
        
        if seq_len != len(quality_string) :
            raise ValueError("Lengths of sequence and quality values differs "
                             " for %s (%i and %i)." \
                             % (title_line, seq_len, len(quality_string)))

        #Return the record and then continue...
        yield (title_line, seq_string, quality_string)
        if not line : return #StopIteration at end of file
    assert False, "Should not reach this line"
        
#This is a generator function!
def FastqPhredIterator(handle, alphabet = single_letter_alphabet, title2ids = None) :
    """Generator function to iterate over FASTQ records (as SeqRecord objects).

     - handle - input file
     - alphabet - optional alphabet
     - title2ids - A function that, when given the title line from the FASTQ
                   file (without the beginning >), will return the id, name and
                   description (in that order) for the record as a tuple of
                   strings.  If this is not given, then the entire title line
                   will be used as the description, and the first word as the
                   id and name.

    Note that use of title2ids matches that of Bio.SeqIO.FastaIO.

    For each sequence in a (Sanger style) FASTQ file there is a matching string
    encoding the PHRED qualities (integers between 0 and about 90) using ASCII
    values with an offset of 33.

    For example, consider a file containing three short reads::

        @EAS54_6_R1_2_1_413_324
        CCCTTCTTGTCTTCAGCGTTTCTCC
        +
        ;;3;;;;;;;;;;;;7;;;;;;;88
        @EAS54_6_R1_2_1_540_792
        TTGGCAGGCCAAGGCCGATGGATCA
        +
        ;;;;;;;;;;;7;;;;;-;;;3;83
        @EAS54_6_R1_2_1_443_348
        GTTGCTTCTGGCGTGGGTGGGGGGG
        +
        ;;;;;;;;;;;9;7;;.7;393333

    For each sequence (e.g. "CCCTTCTTGTCTTCAGCGTTTCTCC") there is a matching
    string encoding the PHRED qualities using a ASCI values with an offset of
    33 (e.g. ";;3;;;;;;;;;;;;7;;;;;;;88").

    Using this module directly you might run:

    >>> handle = open("Quality/example.fastq", "rU")
    >>> for record in FastqPhredIterator(handle) :
    ...     print record.id, record.seq
    EAS54_6_R1_2_1_413_324 CCCTTCTTGTCTTCAGCGTTTCTCC
    EAS54_6_R1_2_1_540_792 TTGGCAGGCCAAGGCCGATGGATCA
    EAS54_6_R1_2_1_443_348 GTTGCTTCTGGCGTGGGTGGGGGGG
    >>> handle.close()

    Typically however, you would call this via Bio.SeqIO instead with "fastq" as
    the format:

    >>> from Bio import SeqIO
    >>> handle = open("Quality/example.fastq", "rU")
    >>> for record in SeqIO.parse(handle, "fastq") :
    ...     print record.id, record.seq
    EAS54_6_R1_2_1_413_324 CCCTTCTTGTCTTCAGCGTTTCTCC
    EAS54_6_R1_2_1_540_792 TTGGCAGGCCAAGGCCGATGGATCA
    EAS54_6_R1_2_1_443_348 GTTGCTTCTGGCGTGGGTGGGGGGG
    >>> handle.close()

    If you want to look at the qualities, they are record in each record's
    per-letter-annotation dictionary as a simple list of integers:

    >>> print record.letter_annotations["phred_quality"]
    [26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 24, 26, 22, 26, 26, 13, 22, 26, 18, 24, 18, 18, 18, 18]
    """
    assert SANGER_SCORE_OFFSET == ord("!")
    for title_line, seq_string, quality_string in FastqGeneralIterator(handle) :
        if title2ids :
            id, name, descr = title2ids(title_line)
        else :
            descr = title_line
            id   = descr.split()[0]
            name = id
        record = SeqRecord(Seq(seq_string, alphabet),
                           id=id, name=name, description=descr)
        qualities = [ord(letter)-SANGER_SCORE_OFFSET for letter in quality_string]
        if qualities and (min(qualities) < 0 or max(qualities) > 93) :
            raise ValueError("PHRED quality score outside 0 to 93 found - "
                             "your file is probably not in the standard "
                             "Sanger FASTQ format. Check if it is one of the"
                             "Solexa/Illumina variants instead.")
        #For speed, will now use a dirty trick to speed up assigning the
        #qualities. We do this to bypass the length check imposed by the
        #per-letter-annotations restricted dict (as this has already been
        #checked by FastqGeneralIterator). This is equivalent to:
        #record.letter_annotations["phred_quality"] = qualities
        dict.__setitem__(record._per_letter_annotations,
                         "phred_quality", qualities)
        yield record

#This is a generator function!
def FastqSolexaIterator(handle, alphabet = single_letter_alphabet, title2ids = None) :
    r"""Parsing old Solexa/Illumina FASTQ like files (which differ in the quality mapping).

    The optional arguments are the same as those for the FastqPhredIterator.

    For each sequence in Solexa/Illumina FASTQ files there is a matching string
    encoding the Solexa integer qualities using ASCII values with an offset
    of 64.  Solexa scores are scaled differently to PHRED scores, and Biopython
    will NOT perform any automatic conversion when loading.

    NOTE - This file format is used by the OLD versions of the Solexa/Illumina
    pipeline. See also the FastqIlluminaIterator function for the NEW version.

    For example, consider a file containing these five records::
        
        @SLXA-B3_649_FC8437_R1_1_1_610_79
        GATGTGCAATACCTTTGTAGAGGAA
        +SLXA-B3_649_FC8437_R1_1_1_610_79
        YYYYYYYYYYYYYYYYYYWYWYYSU
        @SLXA-B3_649_FC8437_R1_1_1_397_389
        GGTTTGAGAAAGAGAAATGAGATAA
        +SLXA-B3_649_FC8437_R1_1_1_397_389
        YYYYYYYYYWYYYYWWYYYWYWYWW
        @SLXA-B3_649_FC8437_R1_1_1_850_123
        GAGGGTGTTGATCATGATGATGGCG
        +SLXA-B3_649_FC8437_R1_1_1_850_123
        YYYYYYYYYYYYYWYYWYYSYYYSY
        @SLXA-B3_649_FC8437_R1_1_1_362_549
        GGAAACAAAGTTTTTCTCAACATAG
        +SLXA-B3_649_FC8437_R1_1_1_362_549
        YYYYYYYYYYYYYYYYYYWWWWYWY
        @SLXA-B3_649_FC8437_R1_1_1_183_714
        GTATTATTTAATGGCATACACTCAA
        +SLXA-B3_649_FC8437_R1_1_1_183_714
        YYYYYYYYYYWYYYYWYWWUWWWQQ
        
    Using this module directly you might run:

    >>> handle = open("Quality/solexa_example.fastq", "rU")
    >>> for record in FastqSolexaIterator(handle) :
    ...     print record.id, record.seq
    SLXA-B3_649_FC8437_R1_1_1_610_79 GATGTGCAATACCTTTGTAGAGGAA
    SLXA-B3_649_FC8437_R1_1_1_397_389 GGTTTGAGAAAGAGAAATGAGATAA
    SLXA-B3_649_FC8437_R1_1_1_850_123 GAGGGTGTTGATCATGATGATGGCG
    SLXA-B3_649_FC8437_R1_1_1_362_549 GGAAACAAAGTTTTTCTCAACATAG
    SLXA-B3_649_FC8437_R1_1_1_183_714 GTATTATTTAATGGCATACACTCAA
    >>> handle.close()

    Typically however, you would call this via Bio.SeqIO instead with "fastq" as
    the format:

    >>> from Bio import SeqIO
    >>> handle = open("Quality/solexa_example.fastq", "rU")
    >>> for record in SeqIO.parse(handle, "fastq-solexa") :
    ...     print record.id, record.seq
    SLXA-B3_649_FC8437_R1_1_1_610_79 GATGTGCAATACCTTTGTAGAGGAA
    SLXA-B3_649_FC8437_R1_1_1_397_389 GGTTTGAGAAAGAGAAATGAGATAA
    SLXA-B3_649_FC8437_R1_1_1_850_123 GAGGGTGTTGATCATGATGATGGCG
    SLXA-B3_649_FC8437_R1_1_1_362_549 GGAAACAAAGTTTTTCTCAACATAG
    SLXA-B3_649_FC8437_R1_1_1_183_714 GTATTATTTAATGGCATACACTCAA
    >>> handle.close()

    If you want to look at the qualities, they are recorded in each record's
    per-letter-annotation dictionary as a simple list of integers:

    >>> print record.letter_annotations["solexa_quality"]
    [25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 23, 25, 25, 25, 25, 23, 25, 23, 23, 21, 23, 23, 23, 17, 17]

    These scores aren't very good, but they are high enough that they map
    almost exactly onto PHRED scores:

    >>> print "%0.2f" % phred_quality_from_solexa(25)
    25.01

    Let's look at faked example read which is even worse, where there are
    more noticeable differences between the Solexa and PHRED scores::

         @slxa_0001_1_0001_01
         ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTNNNNNN
         +slxa_0001_1_0001_01
         hgfedcba`_^]\[ZYXWVUTSRQPONMLKJIHGFEDCBA@?>=<;

    Again, you would typically use Bio.SeqIO to read this file in (rather than
    calling the Bio.SeqIO.QualtityIO module directly).  Most FASTQ files will
    contain thousands of reads, so you would normally use Bio.SeqIO.parse()
    as shown above.  This example has only as one entry, so instead we can
    use the Bio.SeqIO.read() function:

    >>> from Bio import SeqIO
    >>> handle = open("Quality/solexa_faked.fastq", "rU")
    >>> record = SeqIO.read(handle, "fastq-solexa")
    >>> handle.close()
    >>> print record.id, record.seq
    slxa_0001_1_0001_01 ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTNNNNNN
    >>> print record.letter_annotations["solexa_quality"]
    [40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -5]

    These quality scores are so low that when converted from the Solexa scheme
    into PHRED scores they look quite different:

    >>> print "%0.2f" % phred_quality_from_solexa(-1)
    2.54
    >>> print "%0.2f" % phred_quality_from_solexa(-5)
    1.19

    Note you can use the Bio.SeqIO.write() function or the SeqRecord's format
    method to output the record(s):

    >>> print record.format("fastq-solexa")
    @slxa_0001_1_0001_01
    ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTNNNNNN
    +
    hgfedcba`_^]\[ZYXWVUTSRQPONMLKJIHGFEDCBA@?>=<;
    <BLANKLINE>
    
    Note this output is slightly different from the input file as Biopython
    has left out the optional repetition of the sequence identifier on the "+"
    line.  If you want the to use PHRED scores, use "fastq" or "qual" as the
    output format instead, and Biopython will do the conversion for you:

    >>> print record.format("fastq")
    @slxa_0001_1_0001_01
    ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTNNNNNN
    +
    IHGFEDCBA@?>=<;:9876543210/.-,++*)('&&%%$$##""
    <BLANKLINE>
    
    >>> print record.format("qual")
    >slxa_0001_1_0001_01
    40 39 38 37 36 35 34 33 32 31 30 29 28 27 26 25 24 23 22 21
    20 19 18 17 16 15 14 13 12 11 10 10 9 8 7 6 5 5 4 4 3 3 2 2
    1 1
    <BLANKLINE>

    As shown above, the poor quality Solexa reads have been mapped to the
    equivalent PHRED score (e.g. -5 to 1 as shown earlier).
    """
    for title_line, seq_string, quality_string in FastqGeneralIterator(handle) :
        if title2ids :
            id, name, descr = title_line
        else :
            descr = title_line
            id   = descr.split()[0]
            name = id
        record = SeqRecord(Seq(seq_string, alphabet),
                           id=id, name=name, description=descr)
        qualities = [ord(letter)-SOLEXA_SCORE_OFFSET for letter in quality_string]
        #DO NOT convert these into PHRED qualities automatically!
        if qualities and min(qualities) < -5 :
            raise ValueError("Solexa quality score of %i found, less than -5. "
                             "Your file is probably not in the original Solexa "
                             "(or early Illumina) format. Check if it is a "
                             "standard Sanger FASTQ file." % min(qualities))
        #Dirty trick to speed up this line:
        #record.letter_annotations["solexa_quality"] = qualities
        dict.__setitem__(record._per_letter_annotations,
                         "solexa_quality", qualities)
        yield record

#This is a generator function!
def FastqIlluminaIterator(handle, alphabet = single_letter_alphabet, title2ids = None) :
    """Parse new Illumina 1.3+ FASTQ like files (which differ in the quality mapping).

    The optional arguments are the same as those for the FastqPhredIterator.

    For each sequence in Illumina 1.3+ FASTQ files there is a matching string
    encoding PHRED integer qualities using ASCII values with an offset of 64.

    NOTE - Older versions of the Solexa/Illumina pipeline encoded Solexa scores
    with an ASCII offset of 64. They are approximately equal but only for high
    qaulity reads. If you have an old Solexa/Illumina file with negative
    Solexa scores, and try and read this as an Illumina 1.3+ file it will fail:

    >>> from Bio import SeqIO
    >>> record = SeqIO.read(open("Quality/solexa_faked.fastq"), "fastq-solexa")
    >>> print record.id, record.seq
    slxa_0001_1_0001_01 ACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTNNNNNN
    >>> print record.letter_annotations["solexa_quality"]
    [40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -5]
    >>> record2 = SeqIO.read(open("Quality/solexa_faked.fastq"), "fastq-illumina")
    Traceback (most recent call last):
       ...
    ValueError: PHRED quality score outside 0 to 93 found - your file is probably not in the Illumina 1.3+ FASTQ format. Check if it is a standard Sanger FASTQ file or from an older Solexa/Illumina pipeline.

    NOTE - True Sanger style FASTQ files use PHRED scores with an offset of 33.
    """
    for title_line, seq_string, quality_string in FastqGeneralIterator(handle) :
        if title2ids :
            id, name, descr = title2ids(title_line)
        else :
            descr = title_line
            id   = descr.split()[0]
            name = id
        record = SeqRecord(Seq(seq_string, alphabet),
                           id=id, name=name, description=descr)
        qualities = [ord(letter)-SOLEXA_SCORE_OFFSET for letter in quality_string]
        if qualities and (min(qualities) < 0 or max(qualities) > 93) :
            raise ValueError("PHRED quality score outside 0 to 93 found - "
                             "your file is probably not in the Illumina 1.3+ "
                             "FASTQ format. Check if it is a standard Sanger "
                             "FASTQ file or from an older Solexa/Illumina "
                             "pipeline.")
        #Dirty trick to speed up this line:
        #record.letter_annotations["phred_quality"] = qualities
        dict.__setitem__(record._per_letter_annotations,
                         "phred_quality", qualities)
        yield record
    
def QualPhredIterator(handle, alphabet = single_letter_alphabet, title2ids = None) :
    """For QUAL files which include PHRED quality scores, but no sequence.

    For example, consider this short QUAL file::

        >EAS54_6_R1_2_1_413_324
        26 26 18 26 26 26 26 26 26 26 26 26 26 26 26 22 26 26 26 26
        26 26 26 23 23
        >EAS54_6_R1_2_1_540_792
        26 26 26 26 26 26 26 26 26 26 26 22 26 26 26 26 26 12 26 26
        26 18 26 23 18
        >EAS54_6_R1_2_1_443_348
        26 26 26 26 26 26 26 26 26 26 26 24 26 22 26 26 13 22 26 18
        24 18 18 18 18
    
    Using this module directly you might run:

    >>> handle = open("Quality/example.qual", "rU")
    >>> for record in QualPhredIterator(handle) :
    ...     print record.id, record.seq
    EAS54_6_R1_2_1_413_324 ?????????????????????????
    EAS54_6_R1_2_1_540_792 ?????????????????????????
    EAS54_6_R1_2_1_443_348 ?????????????????????????
    >>> handle.close()

    Typically however, you would call this via Bio.SeqIO instead with "qual"
    as the format:

    >>> from Bio import SeqIO
    >>> handle = open("Quality/example.qual", "rU")
    >>> for record in SeqIO.parse(handle, "qual") :
    ...     print record.id, record.seq
    EAS54_6_R1_2_1_413_324 ?????????????????????????
    EAS54_6_R1_2_1_540_792 ?????????????????????????
    EAS54_6_R1_2_1_443_348 ?????????????????????????
    >>> handle.close()

    Becase QUAL files don't contain the sequence string itself, the seq
    property is set to an UnknownSeq object.  As no alphabet was given, this
    has defaulted to a generic single letter alphabet and the character "?"
    used.

    By specifying a nucleotide alphabet, "N" is used instead:

    >>> from Bio import SeqIO
    >>> from Bio.Alphabet import generic_dna
    >>> handle = open("Quality/example.qual", "rU")
    >>> for record in SeqIO.parse(handle, "qual", alphabet=generic_dna) :
    ...     print record.id, record.seq
    EAS54_6_R1_2_1_413_324 NNNNNNNNNNNNNNNNNNNNNNNNN
    EAS54_6_R1_2_1_540_792 NNNNNNNNNNNNNNNNNNNNNNNNN
    EAS54_6_R1_2_1_443_348 NNNNNNNNNNNNNNNNNNNNNNNNN
    >>> handle.close()

    However, the quality scores themselves are available as a list of integers
    in each record's per-letter-annotation:

    >>> print record.letter_annotations["phred_quality"]
    [26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 24, 26, 22, 26, 26, 13, 22, 26, 18, 24, 18, 18, 18, 18]

    You can still slice one of these SeqRecord objects with an UnknownSeq:

    >>> sub_record = record[5:10]
    >>> print sub_record.id, sub_record.letter_annotations["phred_quality"]
    EAS54_6_R1_2_1_443_348 [26, 26, 26, 26, 26]
    """
    #Skip any text before the first record (e.g. blank lines, comments)
    while True :
        line = handle.readline()
        if line == "" : return #Premature end of file, or just empty?
        if line[0] == ">" :
            break

    while True :
        if line[0]!=">" :
            raise ValueError("Records in Fasta files should start with '>' character")
        if title2ids :
            id, name, descr = title2ids(line[1:].rstrip())
        else :
            descr = line[1:].rstrip()
            id   = descr.split()[0]
            name = id

        qualities = []
        line = handle.readline()
        while True:
            if not line : break
            if line[0] == ">": break
            qualities.extend([int(word) for word in line.split()])
            line = handle.readline()

        if qualities :
            if min(qualities) < 0 or max(qualities) > 93 :
                raise ValueError(("Quality score range for %s is %i to %i, "
                                  "outside the expected 0 to 93.  Perhaps "
                                  "these are Solexa/Illumina scores, and not "
                                  "PHRED scores?") \
                                 % (id, min(qualities), max(qualities)))
        
        #Return the record and then continue...
        record = SeqRecord(UnknownSeq(len(qualities), alphabet),
                           id = id, name = name, description = descr)
        #Dirty trick to speed up this line:
        #record.letter_annotations["phred_quality"] = qualities
        dict.__setitem__(record._per_letter_annotations,
                         "phred_quality", qualities)
        yield record

        if not line : return #StopIteration
    assert False, "Should not reach this line"

class FastqPhredWriter(SequentialSequenceWriter):
    """Class to write standard FASTQ format files (using PHRED quality scores).

    Although you can use this class directly, you are strongly encouraged
    to use the Bio.SeqIO.write() function instead.  For example, this code
    reads in a standard Sanger style FASTQ file (using PHRED scores) and
    re-saves it as another FASTQ (PHRED) file:

    >>> from Bio import SeqIO
    >>> record_iterator = SeqIO.parse(open("Quality/example.fastq"), "fastq")
    >>> out_handle = open("Quality/temp.fastq", "w")
    >>> SeqIO.write(record_iterator, out_handle, "fastq")
    3
    >>> out_handle.close()

    You might want to do this if the original file included extra line breaks,
    which while valid may not be supported by all tools.  The output file from
    Biopython will have each sequence on a single line, and each quality
    string on a single line (which is considered desirable for maximum
    compatibility).

    In this next example, an old style Solexa/Illumina FASTQ file (using Solexa
    quality scores) is converted into a standard Sanger style FASTQ file using
    PHRED qualities:

    >>> from Bio import SeqIO
    >>> record_iterator = SeqIO.parse(open("Quality/solexa_example.fastq"), "fastq-solexa")
    >>> out_handle = open("Quality/temp.fastq", "w")
    >>> SeqIO.write(record_iterator, out_handle, "fastq")
    5
    >>> out_handle.close()

    This code is also called if you use the .format("fastq") method of a
    SeqRecord.

    P.S. To avoid cluttering up your working directory, you can delete this
    temporary file now:

    >>> import os
    >>> os.remove("Quality/temp.fastq")
    """
    assert SANGER_SCORE_OFFSET == ord("!")

    def write_record(self, record):
        """Write a single FASTQ record to the file."""
        assert self._header_written
        assert not self._footer_written
        self._record_written = True

        #TODO - Is an empty sequence allowed in FASTQ format?
        qualities = _get_phred_quality(record)
        try :
            #This rounds to the nearest integer:
            qualities_str = "".join([chr(int(round(q+SANGER_SCORE_OFFSET,0))) for q \
                                 in qualities])
        except TypeError, e :
            if None in qualities :
                raise TypeError("A quality value of None was found")
            else :
                raise e
        
        if record.seq is None:
            raise ValueError("No sequence for record %s" % record.id)
        if len(qualities_str) != len(record) :
            raise ValueError("Record %s has sequence length %i but %i quality scores" \
                             % (record.id, len(record), len(qualities_str)))

        #FASTQ files can include a description, just like FASTA files
        #(at least, this is what the NCBI Short Read Archive does)
        id = self.clean(record.id)
        description = self.clean(record.description)
        if description and description.split(None,1)[0]==id :
            #The description includes the id at the start
            title = description
        elif description :
            title = "%s %s" % (id, description)
        else :
            title = id

        self.handle.write("@%s\n%s\n+\n%s\n" % (title, record.seq, qualities_str))

class QualPhredWriter(SequentialSequenceWriter):
    """Class to write QUAL format files (using PHRED quality scores).

    Although you can use this class directly, you are strongly encouraged
    to use the Bio.SeqIO.write() function instead.  For example, this code
    reads in a FASTQ file and saves the quality scores into a QUAL file:

    >>> from Bio import SeqIO
    >>> record_iterator = SeqIO.parse(open("Quality/example.fastq"), "fastq")
    >>> out_handle = open("Quality/temp.qual", "w")
    >>> SeqIO.write(record_iterator, out_handle, "qual")
    3
    >>> out_handle.close()

    This code is also called if you use the .format("qual") method of a
    SeqRecord.

    P.S. Don't forget to clean up the temp file if you don't need it anymore:

    >>> import os
    >>> os.remove("Quality/temp.qual")
    """
    def __init__(self, handle, wrap=60, record2title=None):
        """Create a QUAL writer.

        Arguments:
         - handle - Handle to an output file, e.g. as returned
                    by open(filename, "w")
         - wrap   - Optional line length used to wrap sequence lines.
                    Defaults to wrapping the sequence at 60 characters
                    Use zero (or None) for no wrapping, giving a single
                    long line for the sequence.
         - record2title - Optional function to return the text to be
                    used for the title line of each record.  By default
                    a combination of the record.id and record.description
                    is used.  If the record.description starts with the
                    record.id, then just the record.description is used.

        The record2title argument is present for consistency with the
        Bio.SeqIO.FastaIO writer class.
        """
        SequentialSequenceWriter.__init__(self, handle)
        #self.handle = handle
        self.wrap = None
        if wrap :
            if wrap < 1 :
                raise ValueError
        self.wrap = wrap
        self.record2title = record2title

    def write_record(self, record):
        """Write a single QUAL record to the file."""
        assert self._header_written
        assert not self._footer_written
        self._record_written = True

        if self.record2title :
            title=self.clean(self.record2title(record))
        else :
            id = self.clean(record.id)
            description = self.clean(record.description)

            #if description[:len(id)]==id :
            if description and description.split(None,1)[0]==id :
                #The description includes the id at the start
                title = description
            elif description :
                title = "%s %s" % (id, description)
            else :
                title = id

        assert "\n" not in title
        assert "\r" not in title
        self.handle.write(">%s\n" % title)

        qualities = _get_phred_quality(record)
        try :
            #This rounds to the nearest integer.
            #TODO - can we record a float in a qual file?
            qualities_strs = [("%i" % round(q,0)) for q in qualities]
        except TypeError, e :
            if None in qualities :
                raise TypeError("A quality value of None was found")
            else :
                raise e

        if self.wrap :
            while qualities_strs :
                line=qualities_strs.pop(0)
                while qualities_strs \
                and len(line) + 1 + len(qualities_strs[0]) < self.wrap :
                    line += " " + qualities_strs.pop(0)
                self.handle.write(line + "\n")
        else :
            data = " ".join(qualities_strs)
            self.handle.write(data + "\n")

class FastqSolexaWriter(SequentialSequenceWriter):
    """Write old style Solexa/Illumina FASTQ format files (with Solexa qualities).

    This outputs FASTQ files like those from the early Solexa/Illumina
    pipeline, using Solexa scores and an ASCII offset of 64. These are
    NOT compatible with the standard Sanger style PHRED FASTQ files.

    If your records contain a "solexa_quality" entry under letter_annotations,
    this is used, otherwise any "phred_quality" entry will be used after
    conversion using the solexa_quality_from_phred function. If neither style
    of quality scores are present, an exception is raised.
    
    Although you can use this class directly, you are strongly encouraged
    to use the Bio.SeqIO.write() function instead.  For example, this code
    reads in a FASTQ file and re-saves it as another FASTQ file:

    >>> from Bio import SeqIO
    >>> record_iterator = SeqIO.parse(open("Quality/solexa_example.fastq"), "fastq-solexa")
    >>> out_handle = open("Quality/temp.fastq", "w")
    >>> SeqIO.write(record_iterator, out_handle, "fastq-solexa")
    5
    >>> out_handle.close()

    You might want to do this if the original file included extra line breaks,
    which (while valid) may not be supported by all tools.  The output file
    from Biopython will have each sequence on a single line, and each quality
    string on a single line (which is considered desirable for maximum
    compatibility).

    This code is also called if you use the .format("fastq-solexa") method of
    a SeqRecord.

    P.S. Don't forget to delete the temp file if you don't need it anymore:

    >>> import os
    >>> os.remove("Quality/temp.fastq")
    """
    def write_record(self, record):
        """Write a single FASTQ record to the file."""
        assert self._header_written
        assert not self._footer_written
        self._record_written = True

        #TODO - Is an empty sequence allowed in FASTQ format?
        qualities = _get_solexa_quality(record)
        try :
            qualities_str = "".join([chr(int(round(q+SOLEXA_SCORE_OFFSET,0))) for q \
                                    in qualities])
        except TypeError, e :
            if None in qualities :
                raise TypeError("A quality value of None was found")
            else :
                raise e

        if record.seq is None:
            raise ValueError("No sequence for record %s" % record.id)
        if len(qualities) != len(record) :
            raise ValueError("Record %s has sequence length %i but %i quality scores" \
                             % (record.id, len(record), len(qualities)))

        #FASTQ files can include a description, just like FASTA files
        #(at least, this is what the NCBI Short Read Archive does)
        id = self.clean(record.id)
        description = self.clean(record.description)
        if description and description.split(None,1)[0]==id :
            #The description includes the id at the start
            title = description
        elif description :
            title = "%s %s" % (id, description)
        else :
            title = id

        self.handle.write("@%s\n%s\n+\n%s\n" % (title, record.seq, qualities_str))

class FastqIlluminaWriter(SequentialSequenceWriter):
    """Write Illumina 1.3+ FASTQ format files (with PHRED quality scores).

    This outputs FASTQ files like those from the Solexa/Illumina 1.3+ pipeline,
    using PHRED scores and an ASCII offset of 64. Note these files are NOT
    compatible with the standard Sanger style PHRED FASTQ files which use an
    ASCII offset of 32.

    Although you can use this class directly, you are strongly encouraged to
    use the Bio.SeqIO.write() function with format name "fastq-illumina"
    instead. This code is also called if you use the .format("fastq-illumina")
    method of a SeqRecord.
    """
    def write_record(self, record):
        """Write a single FASTQ record to the file."""
        assert self._header_written
        assert not self._footer_written
        self._record_written = True

        #TODO - Is an empty sequence allowed in FASTQ format?
        qualities = _get_phred_quality(record)
        try :
            qualities_str = "".join([chr(int(round(q+SOLEXA_SCORE_OFFSET,0))) for q \
                                     in qualities])
        except TypeError, e :
            if None in qualities :
                raise TypeError("A quality value of None was found")
            else :
                raise e

        if record.seq is None:
            raise ValueError("No sequence for record %s" % record.id)
        if len(qualities) != len(record) :
            raise ValueError("Record %s has sequence length %i but %i quality scores" \
                             % (record.id, len(record), len(qualities)))

        #FASTQ files can include a description, just like FASTA files
        #(at least, this is what the NCBI Short Read Archive does)
        id = self.clean(record.id)
        description = self.clean(record.description)
        if description and description.split(None,1)[0]==id :
            #The description includes the id at the start
            title = description
        elif description :
            title = "%s %s" % (id, description)
        else :
            title = id

        self.handle.write("@%s\n%s\n+\n%s\n" % (title, record.seq, qualities_str))
        
def PairedFastaQualIterator(fasta_handle, qual_handle, alphabet = single_letter_alphabet, title2ids = None) :
    """Iterate over matched FASTA and QUAL files as SeqRecord objects.

    For example, consider this short QUAL file with PHRED quality scores::

        >EAS54_6_R1_2_1_413_324
        26 26 18 26 26 26 26 26 26 26 26 26 26 26 26 22 26 26 26 26
        26 26 26 23 23
        >EAS54_6_R1_2_1_540_792
        26 26 26 26 26 26 26 26 26 26 26 22 26 26 26 26 26 12 26 26
        26 18 26 23 18
        >EAS54_6_R1_2_1_443_348
        26 26 26 26 26 26 26 26 26 26 26 24 26 22 26 26 13 22 26 18
        24 18 18 18 18
    
    And a matching FASTA file::

        >EAS54_6_R1_2_1_413_324
        CCCTTCTTGTCTTCAGCGTTTCTCC
        >EAS54_6_R1_2_1_540_792
        TTGGCAGGCCAAGGCCGATGGATCA
        >EAS54_6_R1_2_1_443_348
        GTTGCTTCTGGCGTGGGTGGGGGGG

    You can parse these separately using Bio.SeqIO with the "qual" and
    "fasta" formats, but then you'll get a group of SeqRecord objects with
    no sequence, and a matching group with the sequence but not the
    qualities.  Because it only deals with one input file handle, Bio.SeqIO
    can't be used to read the two files together - but this function can!
    For example,
    
    >>> rec_iter = PairedFastaQualIterator(open("Quality/example.fasta", "rU"),
    ...                                    open("Quality/example.qual", "rU"))
    >>> for record in rec_iter :
    ...     print record.id, record.seq
    EAS54_6_R1_2_1_413_324 CCCTTCTTGTCTTCAGCGTTTCTCC
    EAS54_6_R1_2_1_540_792 TTGGCAGGCCAAGGCCGATGGATCA
    EAS54_6_R1_2_1_443_348 GTTGCTTCTGGCGTGGGTGGGGGGG

    As with the FASTQ or QUAL parsers, if you want to look at the qualities,
    they are in each record's per-letter-annotation dictionary as a simple
    list of integers:

    >>> print record.letter_annotations["phred_quality"]
    [26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 24, 26, 22, 26, 26, 13, 22, 26, 18, 24, 18, 18, 18, 18]

    If you have access to data as a FASTQ format file, using that directly
    would be simpler and more straight forward.  Note that you can easily use
    this function to convert paired FASTA and QUAL files into FASTQ files:

    >>> from Bio import SeqIO
    >>> rec_iter = PairedFastaQualIterator(open("Quality/example.fasta", "rU"),
    ...                                    open("Quality/example.qual", "rU"))
    >>> out_handle = open("Quality/temp.fastq", "w")
    >>> SeqIO.write(rec_iter, out_handle, "fastq")
    3
    >>> out_handle.close()

    And don't forget to clean up the temp file if you don't need it anymore:

    >>> import os
    >>> os.remove("Quality/temp.fastq")    
    """
    from Bio.SeqIO.FastaIO import FastaIterator    
    fasta_iter = FastaIterator(fasta_handle, alphabet=alphabet, \
                               title2ids=title2ids)
    qual_iter = QualPhredIterator(qual_handle, alphabet=alphabet, \
                                  title2ids=title2ids)

    #Using zip(...) would create a list loading everything into memory!
    #It would also not catch any extra records found in only one file.
    while True :
        try :
            f_rec = fasta_iter.next()
        except StopIteration :
            f_rec = None
        try :
            q_rec = qual_iter.next()
        except StopIteration :
            q_rec = None
        if f_rec is None and q_rec is None :
            #End of both files
            break
        if f_rec is None :
            raise ValueError("FASTA file has more entries than the QUAL file.")
        if q_rec is None :
            raise ValueError("QUAL file has more entries than the FASTA file.")
        if f_rec.id != q_rec.id :
            raise ValueError("FASTA and QUAL entries do not match (%s vs %s)." \
                             % (f_rec.id, q_rec.id))
        if len(f_rec) != len(q_rec.letter_annotations["phred_quality"]) :
            raise ValueError("Sequence length and number of quality scores disagree for %s" \
                             % f_rec.id)
        #Merge the data....
        f_rec.letter_annotations["phred_quality"] = q_rec.letter_annotations["phred_quality"]
        yield f_rec
    #Done
    

def _test():
    """Run the Bio.SeqIO module's doctests.

    This will try and locate the unit tests directory, and run the doctests
    from there in order that the relative paths used in the examples work.
    """
    import doctest
    import os
    if os.path.isdir(os.path.join("..","..","Tests")) :
        print "Runing doctests..."
        cur_dir = os.path.abspath(os.curdir)
        os.chdir(os.path.join("..","..","Tests"))
        assert os.path.isfile("Quality/example.fastq")
        assert os.path.isfile("Quality/example.fasta")
        assert os.path.isfile("Quality/example.qual")
        assert os.path.isfile("Quality/tricky.fastq")
        assert os.path.isfile("Quality/solexa_faked.fastq")
        doctest.testmod()
        os.chdir(cur_dir)
        del cur_dir
        print "Done"
        
if __name__ == "__main__" :
    _test()

