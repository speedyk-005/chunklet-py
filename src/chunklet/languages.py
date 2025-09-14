"""
This module contains the language sets for the supported sentence splitters.
Each set is filtered to contain only the languages truly unique to that library.
"""

# Complete set of languages supported by pysbd (Python Sentence Boundary Disambiguation)
PYSBD_SUPPORTED_LANGUAGES = {
    "en",  # English
    "mr",  # Marathi
    "hi",  # Hindi
    "bg",  # Bulgarian
    "es",  # Spanish
    "ru",  # Russian
    "ar",  # Arabic
    "am",  # Amharic
    "hy",  # Armenian
    "fa",  # Persian (Farsi)
    "ur",  # Urdu
    "pl",  # Polish
    "zh",  # Chinese (Mandarin)
    "nl",  # Dutch
    "da",  # Danish
    "fr",  # French
    "it",  # Italian
    "el",  # Greek
    "my",  # Burmese (Myanmar)
    "ja",  # Japanese
    "de",  # German
    "kk",  # Kazakh
}

# Languages unique to SentenceSplitter that are NOT supported by pysbd
SENTENCESPLITTER_UNIQUE_LANGUAGES = {
    "ca",  # Catalan
    "cs",  # Czech
    "fi",  # Finnish
    "hu",  # Hungarian
    "is",  # Icelandic
    "lv",  # Latvian
    "lt",  # Lithuanian
    "no",  # Norwegian
    "pt",  # Portuguese
    "ro",  # Romanian
    "sk",  # Slovak
    "sl",  # Slovenian
    "sv",  # Swedish
    "tr",  # Turkish
}

# Languages unique to Sentencex that are NOT supported by pysbd or sentence-splitter
SENTENCESX_UNIQUE_LANGUAGES = {
    "ab",  # Abkhazian
    "abs",  # Ambonese Malay
    "ace",  # Acehnese
    "ady",  # Adyghe
    "aeb",  # Tunisian Arabic
    "aln",  # Gheg Albanian
    "alt",  # Southern Altai
    "ami",  # Amis
    "an",  # Aragonese
    "anp",  # Angika
    "arn",  # Mapudungun
    "arq",  # Algerian Arabic
    "ary",  # Moroccan Arabic
    "arz",  # Egyptian Arabic
    "ast",  # Asturian
    "as",  # Assamese
    "atj",  # Atikamekw
    "av",  # Avar
    "avk",  # Kotava
    "awa",  # Awadhi
    "ay",  # Aymara
    "azb",  # South Azerbaijani
    "ba",  # Bashkir
    "ban",  # Balinese
    "bar",  # Bavarian
    "bbc",  # Batak Toba
    "bcc",  # Southern Balochi
    "be",  # Belarusian
    "bgn",  # Western Balochi
    "bh",  # Bihari
    "bi",  # Bislama
    "bjn",  # Banjar
    "bm",  # Bambara
    "bpy",  # Bishnupriya Manipuri
    "bqi",  # Bakhtiari
    "br",  # Breton
    "btm",  # Batak Mandailing
    "bug",  # Buginese
    "bxr",  # Buryat
    "ce",  # Chechen
    "co",  # Corsican
    "crh",  # Crimean Tatar
    "csb",  # Kashubian
    "cv",  # Chuvash
    "dsb",  # Lower Sorbian
    "dtp",  # Central Dusun
    "dty",  # Dotyali
    "egl",  # Emilian
    "eml",  # Emilian-Romagnol
    "ext",  # Extremaduran
    "ff",  # Fula
    "fit",  # Tornedalen Finnish
    "frc",  # Cajun French
    "frp",  # Arpitan
    "frr",  # Northern Frisian
    "fur",  # Friulian
    "gag",  # Gagauz
    "gan",  # Gan
    "gcr",  # Guianan Creole
    "gl",  # Galician
    "glk",  # Gilaki
    "gn",  # Guaraní
    "gom",  # Goan Konkani
    "gor",  # Gorontalo
    "gsw",  # Swiss German
    "guc",  # Wayuu
    "hak",  # Hakka Chinese
    "hif",  # Fiji Hindi
    "hrx",  # Hunsrik
    "hsb",  # Upper Sorbian
    "ht",  # Haitian Creole
    "ii",  # Nuosu
    "inh",  # Ingush
    "io",  # Ido
    "iu",  # Inuktitut
    "jam",  # Jamaican Patois
    "jut",  # Jutish
    "jv",  # Javanese
    "kaa",  # Karakalpak
    "kab",  # Kabyle
    "kbd",  # Kabardian
    "kbp",  # Kabiyé
    "khw",  # Khowar
    "kiu",  # Kirmanjki
    "kjp",  # Western Pwo Karen
    "kl",  # Kalaallisut
    "ko",  # Korean
    "koi",  # Komi-Permyak
    "krc",  # Karachay-Balkar
    "krl",  # Karelian
    "ks",  # Kashmiri
    "ksh",  # Kölsch
    "ku",  # Kurdish
    "kum",  # Kumyk
    "kv",  # Komi
    "lad",  # Ladino
    "lb",  # Luxembourgish
    "lbe",  # Lak
    "lez",  # Lezgian
    "li",  # Limburgish
    "lij",  # Ligurian
    "liv",  # Livonian
    "lki",  # Laki
    "lld",  # Ladin
    "lmo",  # Lombard
    "ln",  # Lingala
    "lrc",  # Northern Luri
    "ltg",  # Latgalian
    "luz",  # Luri
    "lzh",  # Literary Chinese
    "lzz",  # Laz
    "mad",  # Madurese
    "mai",  # Maithili
    "mdf",  # Moksha
    "mg",  # Malagasy
    "mhr",  # Eastern Mari
    "min",  # Minangkabau
    "mnw",  # Mon
    "mo",  # Moldavian
    "mrj",  # Western Mari
    "mwl",  # Mirandese
    "myv",  # Erzya
    "mzn",  # Mazanderani
    "nah",  # Nahuatl
    "nan",  # Min Nan
    "nap",  # Neapolitan
    "nds",  # Low German
    "nia",  # Nias
    "nn",  # Norwegian Nynorsk
    "nrm",  # Norman
    "oc",  # Occitan
    "olo",  # Livvi-Karelian
    "os",  # Ossetian
    "pcd",  # Picard
    "pdc",  # Pennsylvania German
    "pdt",  # Plautdietsch
    "pfl",  # Palatinate German
    "pih",  # Norfuk
    "pms",  # Piedmontese
    "pnt",  # Pontic Greek
    "qu",  # Quechua
    "qug",  # Chimborazo Highland Quichua
    "rgn",  # Romagnol
    "rmy",  # Romani
    "roa",  # Romagnol
    "rue",  # Rusyn
    "rup",  # Aromanian
    "ruq",  # Megleno-Romanian
    "sa",  # Sanskrit
    "sah",  # Sakha
    "scn",  # Sicilian
    "sco",  # Scots
    "sdc",  # Sassarese Sardinian
    "sdh",  # Southern Kurdish
    "ses",  # Koyraboro Senni
    "sg",  # Sango
    "sgs",  # Samogitian
    "sh",  # Serbo-Croatian
    "shi",  # Tachelhit
    "shy",  # Tachelhit
    "skr",  # Saraiki
    "sli",  # Lower Silesian
    "smn",  # Inari Sami
    "sr",  # Serbian
    "srn",  # Sranan Tongo
    "stq",  # Saterland Frisian
    "sty",  # Siberian Tatar
    "su",  # Sundanese
    "szl",  # Silesian
    "szy",  # Sakiya
    "tay",  # Atayal
    "tcy",  # Tulu
    "tet",  # Tetum
    "tg",  # Tajik
    "trv",  # Taroko
    "tt",  # Tatar
    "ty",  # Tahitian
    "tyv",  # Tuvan
    "udm",  # Udmurt
    "ug",  # Uyghur
    "vec",  # Venetian
    "vep",  # Veps
    "vls",  # West Flemish
    "vmf",  # Main-Franconian
    "vot",  # Votic
    "vro",  # Võro
    "wa",  # Walloon
    "wo",  # Wolof
    "wuu",  # Wu Chinese
    "xal",  # Kalmyk
    "xmf",  # Mingrelian
    "yi",  # Yiddish
    "za",  # Zhuang
    "zea",  # Zeelandic
    "zgh",  # Standard Moroccan Tamazight
    "zu",  # Zulu
}

# Set of all supported languages
SUPPORTED_LANGUAGES = (
    PYSBD_SUPPORTED_LANGUAGES
    | SENTENCESPLITTER_UNIQUE_LANGUAGES
    | SENTENCESX_UNIQUE_LANGUAGES
)

# Print the final, de-duplicated set of languages
print(f"Total languages supported: {len(SUPPORTED_LANGUAGES)}")
print(SUPPORTED_LANGUAGES)
