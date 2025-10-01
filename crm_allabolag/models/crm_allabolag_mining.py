# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from allabolag import Company

# ~ from allabolag.liquidated_companies import iter_liquidated_companies
from allabolag.list import iter_list
from bs4 import BeautifulSoup
import json


import logging

_logger = logging.getLogger(__name__)

MINING_CORPORATE_FORM = [
    ("AB", "Aktiebolag"),
    ("Bankaktiebolag", "Bankaktiebolag"),
    ("Europabolag", "Europabolag"),
    ("Försäkringsaktiebolag", "Försäkringsaktiebolag"),
    ("Medlemsbank", "Medlemsbank"),
    ("Publikt aktiebolag", "Publikt aktiebolag"),
    ("Publikt bankaktiebolag", "Publikt bankaktiebolag"),
    ("Publikt försäkringsaktiebolag", "Publikt försäkringsaktiebolag"),
    ("Sparbank", "Sparbank"),
    ("Tjänstepensionsaktiebolag", "Tjänstepensionsaktiebolag"),
    ("Utländsk banks filial", "Utländsk banks filial"),
    ("Ömsesidigt försäkringsbolag", "Ömsesidigt försäkringsbolag"),
    ("Ömsesidigt tjänstepensionsbolag", "Ömsesidigt tjänstepensionsbolag"),
    ("OVR", "Övriga bolagsformer"),
    ("Allmänna försäkringskassor", "Allmänna försäkringskassor"),
    ("Arbetslöshetskassa", "Arbetslöshetskassa"),
    ("Bostadsförening", "Bostadsförening"),
    ("Bostadsrättsförening", "Bostadsrättsförening"),
    ("Ekonomisk förening", "Ekonomisk förening"),
    ("Enkelt bolag", "Enkelt bolag"),
    ("Europakooperativ", "Europakooperativ"),
    (
        "Europeiska Grupperingar för Territoriellt Samarbete (EGTS)",
        "Europeiska Grupperingar för Territoriellt Samarbete (EGTS)",
    ),
    ("Familjestiftelser", "Familjestiftelser"),
    ("Filial", "Filial"),
    ("Försäkringsförening", "Försäkringsförening"),
    ("Hypoteksförening", "Hypoteksförening"),
    ("Ideell förening", "Ideell förening"),
    ("Juridisk form ej utredd", "Juridisk form ej utredd"),
    ("Kommun", "Kommun"),
    ("Kommunförbund", "Kommunförbund"),
    ("Kooperativ hyresrättsförening", "Kooperativ hyresrättsförening"),
    ("Landsting", "Landsting"),
    (
        "Offentliga korporationer och anstalter",
        "Offentliga korporationer och anstalter",
    ),
    ("Oskiftat dödsbo", "Oskiftat dödsbo"),
    ("Partrederi", "Partrederi"),
    ("Regional statlig myndighet", "Regional statlig myndighet"),
    ("Registrerat trossamfund", "Registrerat trossamfund"),
    ("Sambruksförening", "Sambruksförening"),
    ("Samfällighet", "Samfällighet"),
    ("Statlig enhet", "Statlig enhet"),
    ("Tjänstepensionsförening", "Tjänstepensionsförening"),
    (
        "Understödsföreningar och försäkringsföreningar",
        "Understödsföreningar och försäkringsföreningar",
    ),
    ("Utländsk juridisk person", "Utländsk juridisk person"),
    ("Värdepappersfonder", "Värdepappersfonder"),
    ("Övriga stiftelser eller fonder", "Övriga stiftelser eller fonder"),
    (
        "Övriga svenska juridiska personer bildade enligt särskild lagstiftning",
        "Övriga svenska juridiska personer bildade enligt särskild lagstiftning",
    ),
    ("EF", "Enskild näringsidkare"),
    ("HB/KB", "Handelsbolag eller kommanditbolag"),
    ("Gruvbolag", "Gruvbolag"),
    ("Handelsbolag", "Handelsbolag"),
    ("Kommanditbolag", "Kommanditbolag"),
]

MINING_LAN = [
    ("Blekinge", "Blekinge"),
    ("Dalarna", "Dalarna"),
    ("Gotland", "Gotland"),
    ("Gävleborg", "Gävleborg"),
    ("Halland", "Halland"),
    ("Jämtland", "Jämtland"),
    ("Jönköping", "Jönköping"),
    ("Kalmar", "Kalmar"),
    ("Kronoberg", "Kronoberg"),
    ("Norrbotten", "Norrbotten"),
    ("Skåne", "Skåne"),
    ("Stockholm", "Stockholm"),
    ("Södermanland", "Södermanland"),
    ("Uppsala", "Uppsala"),
    ("Värmland", "Värmland"),
    ("Västerbotten", "Västerbotten"),
    ("Västernorrland", "Västernorrland"),
    ("Västmanland", "Västmanland"),
    ("Västra Götaland", "Västra Götaland"),
    ("Örebro", "Örebro"),
    ("Östergötland", "Östergötland"),
]

MINING_KOMMUN = [
    ("Hällefors", "Hällefors"),
    ("Skövde", "Skövde"),
    ("Eskilstuna", "Eskilstuna"),
    ("Vindeln", "Vindeln"),
    ("Stenungsund", "Stenungsund"),
    ("Nora", "Nora"),
    ("Timrå", "Timrå"),
    ("Lysekil", "Lysekil"),
    ("Nordanstig", "Nordanstig"),
    ("Trollhättan", "Trollhättan"),
    ("Höör", "Höör"),
    ("Färgelanda", "Färgelanda"),
    ("Piteå", "Piteå"),
    ("Skara", "Skara"),
    ("Järfälla", "Järfälla"),
    ("Lessebo", "Lessebo"),
    ("Habo", "Habo"),
    ("Östra Göinge", "Östra Göinge"),
    ("Vaxholm", "Vaxholm"),
    ("Sala", "Sala"),
    ("Degerfors", "Degerfors"),
    ("Sollentuna", "Sollentuna"),
    ("Ludvika", "Ludvika"),
    ("Uddevalla", "Uddevalla"),
    ("Falköping", "Falköping"),
    ("Hedemora", "Hedemora"),
    ("Laholm", "Laholm"),
    ("Åtvidaberg", "Åtvidaberg"),
    ("Lund", "Lund"),
    ("Sundbyberg", "Sundbyberg"),
    ("Härjedalen", "Härjedalen"),
    ("Karlstad", "Karlstad"),
    ("Gnosjö", "Gnosjö"),
    ("Svedala", "Svedala"),
    ("Malå", "Malå"),
    ("Strömsund", "Strömsund"),
    ("Landskrona", "Landskrona"),
    ("Åmål", "Åmål"),
    ("Borås", "Borås"),
    ("Fagersta", "Fagersta"),
    ("Falun", "Falun"),
    ("Kristianstad", "Kristianstad"),
    ("Surahammar", "Surahammar"),
    ("Högsby", "Högsby"),
    ("Vansbro", "Vansbro"),
    ("Umeå", "Umeå"),
    ("Norsjö", "Norsjö"),
    ("Jokkmokk", "Jokkmokk"),
    ("Örnsköldsvik", "Örnsköldsvik"),
    ("Upplands Väsby", "Upplands Väsby"),
    ("Övertorneå", "Övertorneå"),
    ("Bollebygd", "Bollebygd"),
    ("Östersund", "Östersund"),
    ("Pajala", "Pajala"),
    ("Vetlanda", "Vetlanda"),
    ("Kristinehamn", "Kristinehamn"),
    ("Södertälje", "Södertälje"),
    ("Ljusdal", "Ljusdal"),
    ("Ängelholm", "Ängelholm"),
    ("Vårgårda", "Vårgårda"),
    ("Kungsör", "Kungsör"),
    ("Tranemo", "Tranemo"),
    ("Munkfors", "Munkfors"),
    ("Sundsvall", "Sundsvall"),
    ("Orsa", "Orsa"),
    ("Göteborg", "Göteborg"),
    ("Ekerö", "Ekerö"),
    ("Eksjö", "Eksjö"),
    ("Vingåker", "Vingåker"),
    ("Norrköping", "Norrköping"),
    ("Nässjö", "Nässjö"),
    ("Ovanåker", "Ovanåker"),
    ("Ydre", "Ydre"),
    ("Säffle", "Säffle"),
    ("Emmaboda", "Emmaboda"),
    ("Kil", "Kil"),
    ("Ödeshög", "Ödeshög"),
    ("Värnamo", "Värnamo"),
    ("Töreboda", "Töreboda"),
    ("Arvidsjaur", "Arvidsjaur"),
    ("Flen", "Flen"),
    ("Grums", "Grums"),
    ("Arjeplog", "Arjeplog"),
    ("Ronneby", "Ronneby"),
    ("Ljusnarsberg", "Ljusnarsberg"),
    ("Kinda", "Kinda"),
    ("Tranås", "Tranås"),
    ("Ulricehamn", "Ulricehamn"),
    ("Trelleborg", "Trelleborg"),
    ("Hofors", "Hofors"),
    ("Norrtälje", "Norrtälje"),
    ("Oxelösund", "Oxelösund"),
    ("Västerås", "Västerås"),
    ("Sandviken", "Sandviken"),
    ("Åre", "Åre"),
    ("Götene", "Götene"),
    ("Sollefteå", "Sollefteå"),
    ("Hylte", "Hylte"),
    ("Gällivare", "Gällivare"),
    ("Lycksele", "Lycksele"),
    ("Skellefteå", "Skellefteå"),
    ("Motala", "Motala"),
    ("Knivsta", "Knivsta"),
    ("Kungsbacka", "Kungsbacka"),
    ("Markaryd", "Markaryd"),
    ("Kiruna", "Kiruna"),
    ("Gagnef", "Gagnef"),
    ("Vallentuna", "Vallentuna"),
    ("Oskarshamn", "Oskarshamn"),
    ("Simrishamn", "Simrishamn"),
    ("Linköping", "Linköping"),
    ("Partille", "Partille"),
    ("Kävlinge", "Kävlinge"),
    ("Heby", "Heby"),
    ("Dorotea", "Dorotea"),
    ("Vännäs", "Vännäs"),
    ("Nynäshamn", "Nynäshamn"),
    ("Vilhelmina", "Vilhelmina"),
    ("Karlshamn", "Karlshamn"),
    ("Katrineholm", "Katrineholm"),
    ("Kalix", "Kalix"),
    ("Sölvesborg", "Sölvesborg"),
    ("Bjurholm", "Bjurholm"),
    ("Alvesta", "Alvesta"),
    ("Haparanda", "Haparanda"),
    ("Svalöv", "Svalöv"),
    ("Västervik", "Västervik"),
    ("Alingsås", "Alingsås"),
    ("Bengtsfors", "Bengtsfors"),
    ("Filipstad", "Filipstad"),
    ("Ystad", "Ystad"),
    ("Lidingö", "Lidingö"),
    ("Älvdalen", "Älvdalen"),
    ("Årjäng", "Årjäng"),
    ("Köping", "Köping"),
    ("Trosa", "Trosa"),
    ("Sjöbo", "Sjöbo"),
    ("Osby", "Osby"),
    ("Ockelbo", "Ockelbo"),
    ("Hässleholm", "Hässleholm"),
    ("Växjö", "Växjö"),
    ("Torsby", "Torsby"),
    ("Aneby", "Aneby"),
    ("Håbo", "Håbo"),
    ("Lindesberg", "Lindesberg"),
    ("Värmdö", "Värmdö"),
    ("Gnesta", "Gnesta"),
    ("Strängnäs", "Strängnäs"),
    ("Tomelilla", "Tomelilla"),
    ("Härryda", "Härryda"),
    ("Nybro", "Nybro"),
    ("Vänersborg", "Vänersborg"),
    ("Rättvik", "Rättvik"),
    ("Säter", "Säter"),
    ("Sotenäs", "Sotenäs"),
    ("Burlöv", "Burlöv"),
    ("Eda", "Eda"),
    ("Helsingborg", "Helsingborg"),
    ("Bräcke", "Bräcke"),
    ("Huddinge", "Huddinge"),
    ("Nacka", "Nacka"),
    ("Boxholm", "Boxholm"),
    ("Örkelljunga", "Örkelljunga"),
    ("Hörby", "Hörby"),
    ("Grästorp", "Grästorp"),
    ("Salem", "Salem"),
    ("Mjölby", "Mjölby"),
    ("Haninge", "Haninge"),
    ("Luleå", "Luleå"),
    ("Mark", "Mark"),
    ("Olofström", "Olofström"),
    ("Hallstahammar", "Hallstahammar"),
    ("Strömstad", "Strömstad"),
    ("Sunne", "Sunne"),
    ("Karlskoga", "Karlskoga"),
    ("Hammarö", "Hammarö"),
    ("Valdemarsvik", "Valdemarsvik"),
    ("Kumla", "Kumla"),
    ("Åsele", "Åsele"),
    ("Laxå", "Laxå"),
    ("Sävsjö", "Sävsjö"),
    ("Vadstena", "Vadstena"),
    ("Mariestad", "Mariestad"),
    ("Skurup", "Skurup"),
    ("Vaggeryd", "Vaggeryd"),
    ("Östhammar", "Östhammar"),
    ("Botkyrka", "Botkyrka"),
    ("Arvika", "Arvika"),
    ("Staffanstorp", "Staffanstorp"),
    ("Överkalix", "Överkalix"),
    ("Nordmaling", "Nordmaling"),
    ("Gävle", "Gävle"),
    ("Leksand", "Leksand"),
    ("Lilla Edet", "Lilla Edet"),
    ("Vara", "Vara"),
    ("Orust", "Orust"),
    ("Hagfors", "Hagfors"),
    ("Forshaga", "Forshaga"),
    ("Mullsjö", "Mullsjö"),
    ("Svenljunga", "Svenljunga"),
    ("Varberg", "Varberg"),
    ("Sorsele", "Sorsele"),
    ("Malmö", "Malmö"),
    ("Karlskrona", "Karlskrona"),
    ("Norberg", "Norberg"),
    ("Borlänge", "Borlänge"),
    ("Mölndal", "Mölndal"),
    ("Hallsberg", "Hallsberg"),
    ("Nyköping", "Nyköping"),
    ("Ale", "Ale"),
    ("Storfors", "Storfors"),
    ("Bollnäs", "Bollnäs"),
    ("Hudiksvall", "Hudiksvall"),
    ("Borgholm", "Borgholm"),
    ("Storuman", "Storuman"),
    ("Boden", "Boden"),
    ("Essunga", "Essunga"),
    ("Tingsryd", "Tingsryd"),
    ("Lidköping", "Lidköping"),
    ("Enköping", "Enköping"),
    ("Öckerö", "Öckerö"),
    ("Torsås", "Torsås"),
    ("Munkedal", "Munkedal"),
    ("Ljungby", "Ljungby"),
    ("Hultsfred", "Hultsfred"),
    ("Vimmerby", "Vimmerby"),
    ("Tidaholm", "Tidaholm"),
    ("Falkenberg", "Falkenberg"),
    ("Arboga", "Arboga"),
    ("Sigtuna", "Sigtuna"),
    ("Gullspång", "Gullspång"),
    ("Vellinge", "Vellinge"),
    ("Mörbylånga", "Mörbylånga"),
    ("Eslöv", "Eslöv"),
    ("Bjuv", "Bjuv"),
    ("Ånge", "Ånge"),
    ("Tyresö", "Tyresö"),
    ("Hjo", "Hjo"),
    ("Upplands-Bro", "Upplands-Bro"),
    ("Robertsfors", "Robertsfors"),
    ("Tanum", "Tanum"),
    ("Mönsterås", "Mönsterås"),
    ("Halmstad", "Halmstad"),
    ("Tierp", "Tierp"),
    ("Kramfors", "Kramfors"),
    ("Gislaved", "Gislaved"),
    ("Söderköping", "Söderköping"),
    ("Lomma", "Lomma"),
    ("Finspång", "Finspång"),
    ("Malung-Sälen", "Malung-Sälen"),
    ("Mellerud", "Mellerud"),
    ("Avesta", "Avesta"),
    ("Lekeberg", "Lekeberg"),
    ("Höganäs", "Höganäs"),
    ("Smedjebacken", "Smedjebacken"),
    ("Båstad", "Båstad"),
    ("Söderhamn", "Söderhamn"),
    ("Älmhult", "Älmhult"),
    ("Mora", "Mora"),
    ("Nykvarn", "Nykvarn"),
    ("Perstorp", "Perstorp"),
    ("Österåker", "Österåker"),
    ("Karlsborg", "Karlsborg"),
    ("Täby", "Täby"),
    ("Dals-Ed", "Dals-Ed"),
    ("Danderyd", "Danderyd"),
    ("Älvkarleby", "Älvkarleby"),
    ("Berg", "Berg"),
    ("Härnösand", "Härnösand"),
    ("Lerum", "Lerum"),
    ("Klippan", "Klippan"),
    ("Solna", "Solna"),
    ("Tibro", "Tibro"),
    ("Älvsbyn", "Älvsbyn"),
    ("Krokom", "Krokom"),
    ("Skinnskatteberg", "Skinnskatteberg"),
    ("Uppvidinge", "Uppvidinge"),
    ("Kungälv", "Kungälv"),
    ("Tjörn", "Tjörn"),
    ("Herrljunga", "Herrljunga"),
    ("Ragunda", "Ragunda"),
    ("Åstorp", "Åstorp"),
    ("Askersund", "Askersund"),
    ("Bromölla", "Bromölla"),
]

MINING_INDUSTRY = [
    (
        "bransch/ambassader-internationella-org/29/_",
        "Ambassader & Internationella Org.",
    ),
    ("bransch/avlopp-avfall-el-vatten/5/_", "Avlopp, Avfall, El & Vatten"),
    ("bransch/bank-finans-forsakring/14/_", "Bank, Finans & Försäkring"),
    ("bransch/bemanning-arbetsformedling/23/_", "Bemanning & Arbetsförmedling"),
    ("branschbransch-arbetsgivar-yrkesorg/27/_", "Bransch-, Arbetsgivar- & Yrkesorg."),
    (
        "bransch/bygg-design-inredningsverksamhet/6/_",
        "Bygg-, Design- & Inredningsverksamhet",
    ),
    ("bransch/data-it-telekommunikation/13/_", "Data, It & Telekommunikation"),
    ("bransch/detaljhandel/9/_", "Detaljhandel"),
    (("bransch/fastighetsverksamhet/15/_"), ("Fastighetsverksamhet")),
    (("bransch/foretagstjanster/11/_"), ("Företagstjänster")),
    (("bransch/hotell-restaurang/12/_"), ("Hotell & Restaurang")),
    (("bransch/har-skonhetsvard/28/_"), ("Hår & Skönhetsvård")),
    ("bransch/halsa-sjukvard/21/_", "Hälsa & Sjukvård"),
    (
        "bransch/jordbruk-skogsbruk-jakt-fiske/0/_",
        "Jordbruk, Skogsbruk, Jakt & Fiske",
    ),
    (
        ("bransch/juridik-ekonomi-konsulttjanster/16/_"),
        ("Juridik, Ekonomi & Konsulttjänster"),
    ),
    (("bransch/kultur-noje-fritid/26/_"), ("Kultur, Nöje & Fritid")),
    (("bransch/livsmedelsframstallning/2/_"), ("Livsmedelsframställning")),
    (("bransch/media/3/_"), ("Media")),
    (("bransch/motorfordonshandel/7/_"), ("Motorfordonshandel")),
    (
        ("bransch/offentlig-forvaltning-samhalle/25/_"),
        ("Offentlig Förvaltning & Samhälle"),
    ),
    (("bransch/partihandel/8/_"), ("Partihandel")),
    (
        ("bransch/reklam-pr-marknadsundersokning/17/_"),
        ("Reklam, Pr & Marknadsundersökning"),
    ),
    (("bransch/reparation-installation/4/_"), ("Reparation & Installation")),
    (("bransch/resebyra-turism/24/_"), ("Resebyrå & Turism")),
    (("bransch/teknisk-konsultverksamhet/18/_"), ("Teknisk Konsultverksamhet")),
    (("bransch/tillverkning-industri/1/_"), ("Tillverkning & Industri")),
    (("bransch/transport-magasinering/10/_"), ("Transport & Magasinering")),
    (
        "bransch/utbildning-forskning-utveckling/19/_",
        "Utbildning, Forskning & Utveckling",
    ),
    ("bransch/uthyrning-leasing/22/_", "Uthyrning & Leasing"),
    ("bransch/ovriga-konsumenttjanster/20/_", "Övriga Konsumenttjänster"),
]

MINING_INDUSTRY_XV = [
    (("xv/PARTIHANDEL"), ("Partihandel")),
    (("xv/JORDBRUK, SKOGSBRUK, JAKT & FISKE"), ("Jordbruk, skogsbruk, jakt & fiske")),
    (("xv/FASTIGHETSVERKSAMHET"), ("Fastighetsverksamhet")),
    (("xv/BRANSCH-, ARBETSGIVAR- & YRKESORG."), ("Bransch-, arbetsgivar- & yrkesorg.")),
    (
        ("xv/BYGG-, DESIGN- & INREDNINGSVERKSAMHET"),
        ("Bygg-, design- & inredningsverksamhet"),
    ),
    (("/xv/KULTUR, NÖJE & FRITID"), ("Kultur, nöje & fritid")),
    (
        ("/xv/JURIDIK, EKONOMI & KONSULTTJÄNSTER"),
        ("Juridik, ekonomi & konsulttjänster"),
    ),
    (("/xv/DETALJHANDEL"), ("Detaljhandel")),
    (("/xv/DATA, IT & TELEKOMMUNIKATION"), ("Data, it & telekommunikation")),
    (("xv/PARTIHANDEL"), ("Partihandel")),
    (("xv/HÄLSA & SJUKVÅRD"), ("Hälsa & sjukvård")),
    (("xv/TILLVERKNING & INDUSTRI"), ("Tillverkning & industri")),
    (("xv/BANK, FINANS & FÖRSÄKRING"), ("Bank, finans & försäkring")),
    (("xv/UTBILDNING, FORSKNING & UTVECKLING"), ("Utbildning, forskning & utveckling")),
    (("xv/HOTELL & RESTAURANG"), ("Hotell & restaurang")),
    (("/xv/TRANSPORT & MAGASINERING"), ("Transport & magasinering")),
    (("xv/TEKNISK KONSULTVERKSAMHET"), ("Teknisk konsultverksamhet")),
    (("xv/REPARATION & INSTALLATION"), ("Reparation & installation")),
    (("xv/HÅR & SKÖNHETSVÅRD"), ("Hår & skönhetsvård")),
    (("xv/ÖVRIGA KONSUMENTTJÄNSTER"), ("Övriga konsumenttjänster")),
    (("xv/FÖRETAGSTJÄNSTER"), ("Företagstjänster")),
    (("xv/MEDIA"), ("Media")),
    (("xv/REKLAM, PR & MARKNADSUNDERSÖKNING"), ("Reklam, pr & marknadsundersökning")),
    (("xv/BEMANNING & ARBETSFÖRMEDLING"), ("Bemanning & arbetsförmedling")),
    (("xv/MOTORFORDONSHANDEL"), ("Motorfordonshandel")),
    (("/xv/UTHYRNING & LEASING"), ("Uthyrning & leasing")),
    (("xv/AVLOPP, AVFALL, EL & VATTEN"), ("Avlopp, avfall, el & vatten")),
    (("xv/LIVSMEDELSFRAMSTÄLLNING"), ("Livsmedelsframställning")),
    (("xv/RESEBYRÅ & TURISM"), ("Resebyrå & turism")),
    (("xv/OFFENTLIG FÖRVALTNING & SAMHÄLLE"), ("Offentlig förvaltning & samhälle")),
    (("xv/AMBASSADER & INTERNATIONELLA ORG."), ("Ambassader & internationella org.")),
]

MINING_REQUEST_TYPE = [
    ("industry", "Industry"),
    ("lista/omsatter-mest/11", "Turns over the most"),
    ("lista/hogst-resultat/12", "Highest result"),
    ("lista/storsta-arbetsgivarna/13", "Largest employers"),
    ("lista/flest-bilar/14", "Most cars"),
    ("lista/bolag-med-varumarken/15", "Companies with brands"),
    ("lista/bostads-och-bostadsrattfor/25", "Housing Cooperatives"),
    ("lista/statliga-och-kommunala-bolag/33", "State and Municipal Companies"),
]


SNI_MAPPED = {
    "A": ["01", "02", "03"],
    "B": ["05", "06", "07", "08", "09"],
    "C": [str(i).zfill(2) for i in range(10, 34)],
    "D": ["35"],
    "E": ["36", "37", "38", "39"],
    "F": ["41", "42", "43"],
    "G": ["46", "47"],
    "H": ["49", "50", "51", "52", "53"],
    "I": ["55", "56"],
    "J": ["58", "59", "60"],
    "K": ["61", "62", "63"],
    "L": ["64", "65", "66"],
    "M": ["68"],
    "N": [str(i).zfill(2) for i in range(69, 76)],
    "O": [str(i).zfill(2) for i in range(77, 83)],
    "P": ["84"],
    "Q": ["85"],
    "R": ["86", "87", "88"],
    "S": ["90", "91", "92", "93"],
    "T": ["94", "95", "96"],
    "U": ["97", "98"],
    "V": ["99"],
}

SNI_MAIN = [
    ("A", "Jordbruk, skogsbruk och fiske"),
    ("B", "Utvinning av mineral"),
    ("C", "Tillverkning"),
    ("D", "Försörjning av el, gas, värme och kyla"),
    ("E", "Vattenförsörjning; avloppsrening, avfallshantering och sanering"),
    ("F", "Byggverksamhet"),
    ("G", "Handel"),
    ("H", "Transport och magasinering"),
    ("I", "Hotell- och restaurangverksamhet"),
    ("J", "Förlagsverksamhet, Radio- och TV-sändning och distribution"),
    ("K", "Telekommunikation och dataverksamhet"),
    ("L", "Finansiell verksamhet och försäkring"),
    ("M", "Fastighetsverksamhet"),
    ("N", "Juridik, ekonomi, vetenskap och teknik"),
    ("O", "Uthyrning, fastighetsservice och stödverksamhet"),
    ("P", "Offentlig förvaltning och försvar"),
    ("Q", "Utbildning"),
    ("R", "Vård och omsorg; social verksamhet"),
    ("S", "Kultur, idrott och fritid"),
    ("T", "Annan serviceverksamhet"),
    ("U", "Förvärvsarbete i hushåll"),
    ("V", "Internationella organisationer och ambassader"),
]


SNI_TWO = {
    "01": "Jordbruk och jakt samt stödverksamhet i anslutning härtill",
    "02": "Skogsbruk",
    "03": "Fiske och vattenbruk",
    "05": "Kolutvinning",
    "06": "Utvinning av råpetroleum och naturgas",
    "07": "Utvinning av metallmalmer",
    "08": "Annan utvinning av mineral",
    "09": "Stödverksamhet avseende utvinning",
    "10": "Livsmedelsframställning",
    "11": "Framställning av drycker",
    "12": "Tobaksvarutillverkning",
    "13": "Textilvarutillverkning",
    "14": "Tillverkning av kläder",
    "15": "Tillverkning av läder- och skinnvaror och liknande varor av andra material",
    "16": "Tillverkning av trä och varor av trä och kork, utom möbler",
    "17": "Pappers- och pappersvarutillverkning",
    "18": "Grafisk produktion och reproduktion av inspelningar",
    "19": "Tillverkning av stenkolsprodukter och raffinerade petroleumprodukter",
    "20": "Tillverkning av kemikalier och kemiska produkter",
    "21": "Tillverkning av farmaceutiska basprodukter och läkemedel",
    "22": "Tillverkning av gummi- och plastvaror",
    "23": "Tillverkning av andra icke-metalliska mineraliska produkter",
    "24": "Stål- och metallframställning",
    "25": "Tillverkning av metallvaror utom maskiner och apparater",
    "26": "Tillverkning av datorer, elektronikvaror och optik",
    "27": "Tillverkning av elapparatur",
    "28": "Tillverkning av övriga maskiner",
    "29": "Tillverkning av motorfordon, släpfordon och påhängsvagnar",
    "30": "Tillverkning av andra transportmedel",
    "31": "Tillverkning av möbler",
    "32": "Annan tillverkning",
    "33": "Reparation, underhåll och installation av maskiner och utrustning",
    "35": "El-, gas- och ångförsörjning samt luftkonditionering",
    "36": "Vattenförsörjning",
    "37": "Avloppsrening",
    "38": "Insamling av avfall, återvinning och bortskaffande",
    "39": "Sanering, efterbehandling av jord och vatten samt annan verksamhet för föroreningsbekämpning",
    "41": "Byggande av bostadshus och andra byggnader",
    "42": "Anläggningsarbeten",
    "43": "Specialiserad bygg- och anläggningsverksamhet",
    "46": "Parti- och provisionshandel",
    "47": "Detaljhandel",
    "49": "Landtransport; transport i rörsystem",
    "50": "Sjötransport",
    "51": "Lufttransport",
    "52": "Magasinering, varulagring och stödverksamhet avseende transport",
    "53": "Post- och kurirverksamhet",
    "55": "Hotell- och logiverksamhet",
    "56": "Restaurang-, catering- och barverksamhet",
    "58": "Förlagsverksamhet",
    "59": "Film-, video- och tv-programverksamhet, ljudinspelning och musikutgivning",
    "60": "Planering, radio- och tv-sändning, nyhetsbyråer och annan distribution av medieinnehåll",
    "61": "Telekommunikation",
    "62": "Dataprogrammering, datakonsultverksamhet o.d.",
    "63": "Datainfrastruktur, databehandling, hosting och annan informationsverksamhet",
    "64": "Finansiell verksamhet utom försäkrings- och pensionsfondsverksamhet",
    "65": "Försäkrings-, återförsäkrings- och pensionsfondsverksamhet utom obligatorisk socialförsäkring",
    "66": "Stödverksamhet avseende finansiella tjänster och försäkringsverksamhet",
    "68": "Fastighetsverksamhet",
    "69": "Juridisk och ekonomisk konsultverksamhet",
    "70": "Verksamheter som utövas av huvudkontor samt konsultverksamhet avseende företag",
    "71": "Arkitekt- och teknisk konsultverksamhet; teknisk provning och analys",
    "72": "Vetenskaplig forskning och utveckling",
    "73": "Reklamverksamhet, marknadsundersökningar och PR",
    "74": "Annan verksamhet inom juridik, ekonomi, vetenskap och teknik",
    "75": "Veterinärverksamhet",
    "77": "Uthyrning och leasing",
    "78": "Arbetsförmedling, bemanning och annan personalrelaterad verksamhet",
    "79": "Resebyrå- och researrangörsverksamhet samt annan boknings- och reserelaterad verksamhet",
    "80": "Säkerhets- och bevakningsverksamhet",
    "81": "Fastighetsrelaterad stödverksamhet samt skötsel och underhåll av grönytor",
    "82": "Kontorstjänster och annan stödverksamhet till företag",
    "84": "Offentlig förvaltning och försvar; obligatorisk socialförsäkring",
    "85": "Utbildning",
    "86": "Hälso- och sjukvård",
    "87": "Vård och omsorg med boende",
    "88": "Öppna sociala insatser",
    "90": "Konstnärligt skapande och scenkonst",
    "91": "Biblioteks-, arkiv- och museiverksamhet m.m.",
    "92": "Spel- och vadhållningsverksamhet",
    "93": "Sport-, fritids- och nöjesverksamhet",
    "94": "Intressebevakning; religiös verksamhet",
    "95": "Reparation och underhåll av datorer, hushållsartiklar och varor för personligt bruk samt motorfordon och motorcyklar",
    "96": "Konsumenttjänster",
    "97": "Förvärvsarbete i hushåll",
    "98": "Hushållens produktion av diverse varor och tjänster för eget bruk",
    "99": "Verksamhet vid internationella organisationer, utländska ambassader o.d.",
}


MINING_CORPORATE_FORM = [
    (("xb/EF"), ("Enskild firma")),
    (("xb/AB"), ("Aktiebolag")),
    (("xb/IF"), ("Ideella föreningar")),
    (("xb/HK"), ("Hb & Kb")),
    (("xb/OV"), ("Övriga bolagsformer")),
    (("xb/SA"), ("Samfälligheter")),
    (("xb/SF"), ("Sambruksförening")),
    (("xb/FI"), ("Filialer")),
    (("xb/EK"), ("Ekonomisk förening")),
    (("xb/EB"), ("Enkla bolag")),
    (("xb/SK"), ("Statliga & kommunala")),
    (("xb/BF"), ("Bostadsförening")),
    (("xb/VP"), ("Värdepappersfonder")),
]


class CrmLead(models.Model):
    _inherit = "crm.lead"

    mining_id = fields.Many2one(comodel_name="crm.allabolag.mining")

    mining_corporate_form = fields.Selection(
        selection=MINING_CORPORATE_FORM,
        string="Company form",
        related="mining_id.corporate_form",
        readonly=True,
        store=True,
    )
    mining_industry = fields.Selection(
        selection=SNI_MAIN,
        string="industry",
        related="mining_id.industry",
        readonly=True,
        store=True,
    )
    mining_industry_xv = fields.Selection(
        selection=MINING_INDUSTRY_XV,
        string="industry",
        related="mining_id.industry_xv",
        readonly=True,
        store=True,
    )
    mining_lan = fields.Selection(
        selection=MINING_LAN,
        string="County",
        related="mining_id.lan",
        readonly=True,
        store=True,
    )
    mining_kommun = fields.Selection(
        selection=MINING_KOMMUN,
        string="Municipality",
        related="mining_id.kommun",
        readonly=True,
        store=True,
    )
    mining_request_type = fields.Selection(
        selection=MINING_REQUEST_TYPE,
        string="Request Type",
        store=True,
        related="mining_id.request_type",
        readonly=True,
    )


class CrmAllabolagMining(models.Model):
    _name = "crm.allabolag.mining"
    _inherit = ["mail.thread", "mail.activity.mixin", "utm.mixin"]
    _description = "CRM Allabolag Mining"
    _order = "date desc"

    def dynamic_industry_sub(self):
        _logger.warning(f"dynamic_industry_sub {self=}")
        result = []
        for main_code, main_name in SNI_MAIN:
            result.append((main_code, f"{main_code}  {main_name}"))
            for sub_code in SNI_MAPPED.get(main_code, []):
                sub_name = SNI_TWO.get(sub_code, "Okänt")
                result.append((sub_code, f"{sub_code} {sub_name}"))
        return result

    company_currency = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        default=lambda self: self.env.company.id,
    )
    corporate_form = fields.Selection(
        selection=MINING_CORPORATE_FORM, string="Company form"
    )
    date = fields.Date(
        string="Date", default=fields.Date.today()
    )  # fields.date.add|context_today|end_of|start_of|substract|to_date|to_string|today
    description = fields.Text("Notes")
    expected_revenue = fields.Monetary(
        "Expected Revenue", currency_field="company_currency", tracking=True
    )
    employees_from = fields.Integer("Revenue From")
    employees_to = fields.Integer("Revenue To")
    industry = fields.Selection(
        selection=dynamic_industry_sub, string="Industry", required=False
    )
    # ~ industry_sub = fields.Selection(selection=dynamic_industry_sub,string='Industry two numbers',Xcompute='_industry_sub',required=False)
    industry_xv = fields.Selection(selection=MINING_INDUSTRY_XV, string="Industry")
    lan = fields.Selection(selection=MINING_LAN, string="County")
    lead_count = fields.Integer(
        string="Number of Leads", compute="_compute_lead_count", readonly=True
    )
    lead_ids = fields.One2many(
        comodel_name="crm.lead", inverse_name="mining_id", string="Leads", help=""
    )
    leads_url = fields.Char(string="Url", trim=True, compute="_compute_leads_url")
    max_no_leads = fields.Integer(string="Number of Wanted Leads", default=50)
    name = fields.Char(
        "Request",
        index=True,
        required=True,
        compute="_compute_name",
        readonly=False,
        store=True,
    )
    no_employees = fields.Selection(
        selection=[
            ("0-0", "0"),
            ("1-4", "1 - 4"),
            ("5-9", "5 - 9"),
            ("10-19", "10 - 19"),
            ("20-49", "20 - 49"),
            ("50-99", "50 - 99"),
            ("100-199", "100 - 199"),
            ("200-999", "200 - 999"),
            ("1000-1000000", "> 1000"),
        ],
        string="Number of Employees",
    )
    kommun = fields.Selection(selection=MINING_KOMMUN, string="Municipality")
    recurring_plan = fields.Many2one(
        "crm.recurring.plan",
        string="Recurring Plan",
        groups="crm.group_use_recurring_revenues",
    )
    recurring_revenue = fields.Monetary(
        "Recurring Revenues",
        currency_field="company_currency",
        groups="crm.group_use_recurring_revenues",
    )
    request_type = fields.Selection(
        selection=MINING_REQUEST_TYPE,
        string="Request Type",
        required=True,
        default="industry",
    )
    revenue_from = fields.Integer(string="Revenue")
    revenue_to = fields.Integer(string="Revenue")
    profit_from = fields.Integer(string="Profit")
    profit_to = fields.Integer(string="Profit")
    selected_count = fields.Integer(string="Max Number of Leads")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("list", "List"),
            ("done", "Done"),
            ("error", "Error"),
            ("cancel", "Cancel"),
        ],
        default="draft",
        tracking=True,
    )
    tag_ids = fields.Many2many(
        comodel_name="crm.tag", string="Tags", help="Set this tags to created leads"
    )  # relation|column1|column2
    type = fields.Selection(
        selection=[("lead", "Lead"), ("opportunity", "Opportunity")],
        string="Lead Type",
        default="lead",
        required=True,
    )
    team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Sales Team",
        index=True,
        compute="_compute_team_id",
        readonly=False,
        store=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        index=True,
        tracking=True,
        default=lambda self: self.env.user,
    )

    @api.depends("user_id", "industry", "request_type")
    def _compute_name(self):
        for s in self:
            if s.request_type != "industry":
                request_name = [
                    a
                    for a in s.fields_get(allfields=["request_type"])["request_type"][
                        "selection"
                    ]
                    if a[0] == s.request_type
                ][0][1]
                s.name = _(f"[{s.user_id.name}] {request_name}")

    @api.depends("lead_ids")
    def _compute_lead_count(self):
        for s in self:
            s.lead_count = len(s.lead_ids)

    @api.depends(
        "request_type",
        "corporate_form",
        "no_employees",
        "lan",
        "industry",
        "revenue_from",
        "revenue_to",
        "industry_xv",
    )
    def _compute_leads_url(self):
        """When changing the request info also update url"""
        for lead in self:
            segment = []
            if lead.industry:
                segment.append("naceIndustry=" + lead.industry)
            if lead.corporate_form:
                segment.append("companyType=" + lead.corporate_form)

            if lead.no_employees:
                (lead.employees_from, lead.employees_to) = lead.no_employees.split("-")
            if lead.employees_from:
                segment.append(f"numEmployeesFrom={lead.employees_from}")
            if lead.employees_to:
                segment.append(f"numEmployeesTo={lead.employees_to}")

            if lead.revenue_from:
                segment.append(f"revenueFrom={lead.revenue_from}")
            if lead.revenue_to:
                segment.append(f"revenueTo={lead.revenue_to}")
            if lead.profit_from:
                segment.append(f"profitFrom={lead.profit_from}")
            if lead.profit_to:
                segment.append(f"profitTo={lead.profit_to}")

            if lead.kommun and lead.lan:
                segment.append(f"location={lead.kommun},{lead.lan}")
            elif lead.kommun:
                segment.append("location=" + lead.kommun)
            elif lead.lan:
                segment.append("location=" + lead.lan)

            lead.leads_url = "segmentering?" + "&".join(segment)

    @api.depends("user_id", "type")
    def _compute_team_id(self):
        """When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of."""
        for lead in self:
            # setting user as void should not trigger a new team computation
            if not lead.user_id:
                continue
            user = lead.user_id
            if lead.team_id and user in lead.team_id.member_ids | lead.team_id.user_id:
                continue
            team_domain = (
                [("use_leads", "=", True)]
                if lead.type == "lead"
                else [("use_opportunities", "=", True)]
            )
            team = self.env["crm.team"]._get_default_team_id(
                user_id=user.id, domain=team_domain
            )
            lead.team_id = team.id

    def action_get_lead_action(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_all_leads")
        action["domain"] = [("id", "in", self.lead_ids.ids), ("type", "=", "lead")]
        action["help"] = _(
            """<p class="o_view_nocontent_empty_folder">
            No leads found
        </p><p>
            No leads could be generated according to your search criteria
        </p>"""
        )
        return action

    def action_get_opportunity_action(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "crm.crm_lead_opportunities"
        )
        action["domain"] = [
            ("id", "in", self.lead_ids.ids),
            ("type", "=", "opportunity"),
        ]
        action["help"] = _(
            """<p class="o_view_nocontent_empty_folder">
            No opportunities found
        </p><p>
            No opportunities could be generated according to your search criteria
        </p>"""
        )
        return action

    def action_draft(self):
        self.ensure_one()
        self.lead_ids.unlink()
        self.state = "draft"
        return None

    def action_enrich(self):
        self.ensure_one()
        for lead in self.lead_ids:
            if lead.summary_revenue == 0.0:
                try:
                    lead.enrich_allabolag()
                except Exception as e:
                    _logger.warning(f"Allabolag: An unexpected error occurred: {e}")
                    self.state = "error"
                    self.message_post(
                        body=_(f"An unexpected error occurred for {lead.name}: {e}")
                    )
                    return None

        self.state = "done"
        if self.type == "lead":
            action = self.env["ir.actions.actions"]._for_xml_id(
                "crm.crm_lead_all_leads"
            )
            action["domain"] = [("id", "in", self.lead_ids.ids), ("type", "=", "lead")]
        else:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "crm.crm_lead_opportunities"
            )
            action["domain"] = [
                ("id", "in", self.lead_ids.ids),
                ("type", "=", "opportunity"),
            ]
        action["help"] = _(
            """<p class="o_view_nocontent_empty_folder">
            No opportunities found
        </p><p>
            No opportunities could be generated according to your search criteria
        </p>"""
        )
        return action

    def allabolag_search_result(self, page=None):
        if not self.leads_url:
            return None  # Return None instead of 0

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        url_path = self.leads_url
        if page and page > 1:
            url_path = f"{self.leads_url}&page={page}"

        url = f"https://allabolag.se/{url_path}"
        _logger.info(f"Scraping: {url}")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")

        except Exception as e:
            _logger.error(f"Failed to scrape {url}: {e}")
            return None  # Return None instead of 0

    def scrape_traffar_number(self):
        """Scrape number of companies from Allabolag search results."""
        self.ensure_one()

        search_result = self.allabolag_search_result()
        if not search_result:  # Check if we got a valid result
            return 0

        header = search_result.find(class_="SearchResultList-listHeader")
        if header:
            digits = "".join(filter(lambda c: c.isdigit(), header.get_text(strip=True)))
            return int(digits) if digits else 0
        return 0

    def action_check(self):
        self.ensure_one()
        self.selected_count = self.scrape_traffar_number()
        if self.max_no_leads > self.selected_count:
            self.max_no_leads = self.selected_count

    def _get_search_except(self, search_result):
        """Extract organization numbers and URLs from search results."""
        if not search_result:
            return []

        results = []

        # Find all company cards
        company_cards = search_result.find_all(
            class_="SegmentationSearchResultCard-card"
        )

        for card in company_cards:
            try:
                # Extract company name and URL from the h2 link
                name_link = card.find("h2").find("a")
                if name_link:
                    company_name = name_link.get_text(strip=True)
                    company_url = name_link.get("href")

                    # Find the span containing "Org.nr" text
                    org_nr = None
                    property_spans = card.find_all(
                        "span", class_="CardHeader-propertyList"
                    )

                    for prop_span in property_spans:
                        # Check if this span contains the Org.nr
                        inner_spans = prop_span.find_all("span")
                        for inner_span in inner_spans:
                            if inner_span.get_text(strip=True) == "Org.nr":
                                # Get the next sibling text (the actual org number)
                                org_nr = inner_span.next_sibling
                                if org_nr:
                                    org_nr = str(org_nr).strip()
                                break
                        if org_nr:
                            break

                    if org_nr and company_url:
                        results.append(
                            {"name": company_name, "org_nr": org_nr, "url": company_url}
                        )

            except Exception as e:
                _logger.error(f"Failed to extract company data: {e}")
                continue
        return results

    def _get_max_companies_from_search(self):
        """Collect all companies up to max_no_leads by paginating through results."""
        all_companies = []
        page = 1

        while len(all_companies) < self.max_no_leads:
            # Get search results for current page
            search_result = self.allabolag_search_result(page=page)

            if not search_result:
                break

            # Extract companies from this page
            page_companies = self._get_search_except(search_result)

            if not page_companies:
                _logger.info(f"No more results found on page {page}")
                break

            # Add only what we need
            remaining = self.max_no_leads - len(all_companies)
            all_companies.extend(page_companies[:remaining])

            _logger.info(
                f"Page {page}: found {len(page_companies)} companies, total collected: {len(all_companies)}"
            )

            # Check if this was the last page (less than 10 results)
            if len(page_companies) < 10:
                break

            page += 1

            # Safety limit to prevent infinite loops
            if page > 100:
                _logger.warning("Reached maximum page limit (100)")
                break

        _logger.info(
            f"Collected {len(all_companies)} companies out of {self.max_no_leads} requested"
        )
        return all_companies

    def action_submit(self):
        self.ensure_one()
        search_data = self._get_max_companies_from_search()
        try:
            for data in search_data:
                if company_data := self._get_company_details(data.get("org_nr", False)):
                    company_vals = self._set_company_details(company_data)
                    company_vals["linkTo"] = f"https://allabolag.se/{data['url']}"
                    self._sync_lead(company_vals=company_vals)
                    # self.env['crm.lead'].create(company_vals)
                    self.env.cr.commit()
        except Exception as e:
            _logger.warning(f"Allabolag: An unexpected error occurred: {e}")
            self.message_post(
                body=_(f"An unexpected error occurred: {e}"),
                message_type="notification",
            )
            self.state = "error"

        self.state = "list"
        if self.type == "lead":
            return self.action_get_lead_action()
        elif self.type == "opportunity":
            return self.action_get_opportunity_action()
        return None

    def _sync_lead(self, company_vals):
        crm_lead = self.env["crm.lead"]
        lead_id = crm_lead.search(
            [("company_registry", "=", company_vals.get("company_registry"))]
        )
        if not lead_id:
            self.env["crm.lead"].create(company_vals)

    def _set_company_details(self, company_data):
        return {
            "name": company_data.get("name"),
            "partner_name": company_data.get("name", False),
            "company_registry": company_data.get("orgnr", False),
            "mining_id": self.id,
            "city": company_data.get("postalAddress", {}).get("postPlace", False),
            "tag_ids": self.tag_ids,
            "type": self.type,
            "user_id": self.user_id.id if self.user_id else None,
            "description": self.description,
            "team_id": self.team_id.id if self.team_id else None,
            "campaign_id": self.campaign_id.id if self.campaign_id else None,
            "source_id": self.source_id.id if self.source_id else None,
            "medium_id": self.medium_id.id if self.medium_id else None,
            "expected_revenue": self.expected_revenue,
        }

    def _get_company_details(self, org_nr):
        if data := Company(org_nr).data:
            return data.get("company")
        return {}

    def action_allabolag_url(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"https://allabolag.se/{self.leads_url}",
            "target": "new",
        }
