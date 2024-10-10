from random import sample
from .console import console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.layout import Layout
from rich.padding import Padding
from typer import Typer

import textwrap

app = Typer()


@app.callback(invoke_without_command=True)
def print_random_quote():

    width = console.size.width

    if width < 12 + PADDING * 2:
        return

    quote = sample(QUOTES, 1)[0]
    index = QUOTES.index(quote)

    lines = [""]

    paragraphs = [""]
    for c in quote:
        if c == "\n":
            paragraphs.append("")
        else:
            paragraphs[-1] += c

    for i, paragraph in enumerate(paragraphs):

        if len(paragraph) == 0:
            lines.append("")
            continue

        if i == 0:
            first_padding = " " * PADDING
        else:
            first_padding = " " * (PADDING + 1)

        subsequent_padding = " " * (PADDING + 1)

        if i == 0:
            paragraph = f'"{paragraph}'

        if i + 1 == len(paragraphs):
            paragraph = f'{paragraph}"'

        lines += textwrap.wrap(
            paragraph,
            width=width - PADDING,
            replace_whitespace=False,
            initial_indent=first_padding,
            subsequent_indent=subsequent_padding,
        )

    lines.append("")

    longest = max(len(l) for l in lines)
    signoff = f"-CONFUCIUS #{index+1}"
    lines.append(" " * (longest - len(signoff)) + f"[italic]{signoff}[reset]")

    lines.append("")

    for line in lines:
        console.print(line, highlight=False)


PADDING = 6

QUOTES = [
    "DO IT TOMORROW",
    "DO DFT TOMORROW",
    "HOW 'BOUT NAH",
    "STYLE OVER SUBSTANCE",
    "I'M NOT CHINESE",
    "TO DRIVE A TANK SIMPLY USE DRUIDRY TO TRANSFORM INTO A TANK DRIVER",
    "IF THE GAUSSIAN FAILS TWICE CONSECUTIVELY, GIVE UP",
    "THE FEWER HOURS YOU WORK ON A FIXED SALARY THE HIGHER YOUR HOURLY PAY",  # MW
    "COMP. CHEM IS TEMPORARY. CONFUCIUS IS FOREVER",
    "BETTER TO ASK FOR FORGIVENESS THAN PERMISSION",
    "DO YOU THINK I WANT TO BE HERE?",
    "READ THE FUCKING MANUAL",
    "NEVER GIVE A COW FREE MILK",
    "FOR BETTER OR FOR WORSE I'LL ALWAYS HAVE ANOTHER COFFEE",  # MW
    "I'M A BIG PROPONENT FOR HAVING FUN",  # MW
    "I WOULDN'T BET MY LIFE ON IT",
    "DEATH DOES NOT PROTECT YOU FROM CRITICISM",
    "SOMETIMES YOU HAVE TO SPEND MONEY TO MAKE MONEY.\n\nSOMETIMES YOU HAVE TO SPEND MONEY TO LOSE MONEY.\n\nONE THING'S FOR SURE, YOU HAVE TO SPEND MONEY.",  # Rust Valley Restorers
    "PREMATURE JOB FAILURE IS NOTHING TO BE ASHAMED OF",
    "LOUIE TOLD ME WHAT TO DO AND I DID MY BEST TO FUCK IT UP",
    "IT IS IMPOSSIBLE TO REVERSE THE CREATION OF A CAKE",
    "CAKE CAN BE CREATED AND DESTROYED",
    "I CAN HEAR BUT I CAN'T LISTEN",
    "I'M BETTER THAN THE MANUAL",
    "BEFORE TRYING, CONSULT ME",
    "CODE FIRST, THINK LATER",
    "WHEN IN DOUBT, CROSS PRODUCT",
    "CHEMIS[bold]DO[/bold] OR CHEMIS[bold]DON'T[/bold] THERE IS NO CHEMIS[bold]TRY[/bold]",
    "I HATE IT HERE",
    "I DIDN'T SIGN UP FOR THIS",
    "I DON'T UNDERSTAND WHY PEOPLE WOULD CHOOSE TO BE A BIOLOGIST",
    "I HATE PAST ME",
    "SOUNDS LIKE A FUTURE ME PROBLEM",
    "I STRUGGLE TO FIND PEACE",
    "I HEREBY CLASSIFY THIS AS A ROYAL BALL ACHE",
    "I'M ALL OUT OF PASSION",
    "WHAT IS A DECIMAL PLACE BETWEEN FRIENDS?",
    "[bold italic]OF COURSE",
    "[dodger_blue2 bold] 🇬🇷  OF COURSE [/bold /dodger_blue2]",
    "ΩΦ KΩΥΡΣΕ",
    "FRENCH? SO YOU'RE EASY TO SATISFY",
    "YOU DON'T WANT TO FINISH TOO EARLY",
    "BOLD AND UNPROVEN",
    "WHERE IS MY GIRAFFE??",  # CV
    "THIS IS A HIPPOPOTAMUS",
    "MONOGAMOUS ENTANGLEMENT",
    "INVEST IN A STRAP-ON",
    "[bold italic]FRIZZ OFF",  # AC
    "I'M FRIZZED OFF",  # AC
    "I'M GONNA GO TO THAT BUS STATION TOMORROW AND KICK MIKE'S ASS",
    "STRUGGLING FROM SUCCESS",
    "I'D SHOW YOU MINE; BUT I DON'T THINK YOU'D LIKE IT",
    "I'M SEVERAL RAKI'S DEEP",
    "DON'T ASK ME QUESTIONS THAT COULD HAVE CONSEQUENCES",
    "ENORMOUS DRAGON OF FAECES, DANCING INSIDE ME",  # FB
    "I HAD A CRISIS OF FAITH IN MY RESEARCH, BUT THEN I REALISED THAT IT'S FINE",
    "IT DEPENDS",
    "KIND OF A PROOF",
    "THE DEAD CAT CAN BE A RESOURCE",
    "WITH A TALK LIKE THAT YOU CAN EXPECT TO MEET A PERSON\nWHO TOTALLY DISAGREES WITH EVERYTHING YOU SAID.\nYOU WILL FIND THAT PERSON IN ME",  # Moritz @ QuEBS 2022
    "MIDNIGHT MEAT",
    "EXISTENCE IS CANCER",
    "IT'S A PITY THEY FOUND A CURE FOR LEPROSY",  # QuEBS 2022 Excursion
    "[bold italic]MEOW",  # RG
    "DON’T KNOW DON’T CARE",
    "INTERESTING TRANSFER DOWN THESE RODS",
    # "DISSEMINATE THROUGHOUT THE UK",
    "DUMPING MY PUMP ON",
    "KINDA TOXIC, BUT DON’T WORRY ABOUT THAT",
    "WHACKING GREAT ABSORBER",  # AM
    "I KNOW YOU’RE THEORISTS, AND THIS IS VERY MUDDY",
    "I HAVE A PROPENSITY FOR THE DENSITY",  # AB @ QuEBS 2022
    "OH MY [bold]GOODNESS[/bold]",  # GF
    "YOU ARE UNDERMINING MY AUTHORITY",  # unknown @ QuEBS 2022
    "TO BE WEAK, IS ACTUALLY AN ADVANTAGE ",
    "SPEEDY BOARDING",
    "THE PHILOSOPHICAL SIGNIFICANCE OF POO",
    "THE CAFFEINE IS A MATTER OF LIFE AND DEATH ",
    "IT’S ALMOST CERTAINLY WRONG, BUT FUN",
    "THAT WOULD HAVE BEEN WISE, HOWEVER, I AM NOT A WISE MAN",
    "THAT MAKES YOU THINK SOFT",
    "I WOULD ARGUE THAT BARE LEGS IS BETTER",
    "ANYTHING IS MICROSCOPIC IF IT’S FAR AWAY ENOUGH",
    "AN ERROR OCCURRED, HOW IS THAT EVEN SCIENTIFICALLY POSSIBLE",
    "YOU HEAR THAT? THAT’S A TARDIGRADE",
    "I SEEM TO HAVE LOST CONTROL [OF MY MOUSE]",
    "THERE’S NO ANSWER, BY THE WAY",
    "BECAUSE OF SOME PHYSICS ",
    "PSEUDO-WEAK",
    "THESE BALLS ARE JUST REGULAR SHINY",  # MW
    "THE LAST COUP KIND OF FIZZLED OUT",
    "I THINK IT’S STRAIGHT SO IT MUST BE ERADICATED",
    "KOBE BEEF IS ALSO FAMOUSLY DEAD COW",
    "I’VE ALSO DECIDED I AM NOT A MORAL PERSON",
    "IT WAS ONLY AN EMPTY THREAT",  # JJMF
    "THREATS ARE A PART OF WORKING LIFE",  # JJMF
    "WELL THE THREAT WORKED!",  # JJMF
    "AN EMPTY THREAT IS STILL A THREAT",
    "WHAT DO YOU THINK I’M SOME SORT OF PEPSI CRACK WHORE?",
    "LOW IMPACT FACTOR? I WANT LOW IMPACT ON MY LIFE!",
    "NOT F*CK YO MAMA F*CK YO-YO MA!",
    "I FORGOT ABOUT THE PASSAGE OF TIME",
    "EVERYTHING IS JUST A BIG WEIRD LIGAND",
    "IT NEEDS TO TASTE GOOD, AND KILL YOU",  # CV
    "MY ABILITY TO SEE FUNKINESS REQUIRES EXPERIENCE",  # ISQBP 2022
    "HISTIDINE IS A PROBLEM",
    "I HATE THE FACT THAT THEY SPENT SO MUCH TIME ON THESE QUOTES, INSTEAD OF IMPROVING THEIR SIMULATION SOFTWARE",  # Gromacs
    "BUTTER MUSS SEIN",
    "I DON’T NEED A CONTROL BECAUSE I DON’T HAVE ANY RESULTS",
    "LET THE ANIMAL EAT FIBRE, AND THEN EAT THE ANIMAL",
    "THAT’S NOT A SHOT MATE!!",
    "FUCK AROUND AND FIND OUT",
    "♫♬♪[bold]OH MON BEBE[/bold]",  # Les Kaira
    "WHY DID TOM CHEATHAM KILL US LAST NIGHT?",  # ISQBP 2022
    "NOSE-HOOVER? SO LIKE A COCAINE ADDICT?",
    "YOU CAN SLEEP ON A BANANA",
    "AMBER AND I BROKE UP",  # MW
    "WE WENT TOO FAR",
    "THEY GOT JIGGLY PHYSICS?",
    "DO YOU WANT TO SEE MY STUFF JIGGLING?",
    "WE DON’T SEE COLOURS HERE, WE JUST SEE BALLS",
    "IN MY OPINION THIS IS EXACTLY WHAT IS WRONG WITH SCIENCE",
    "I DIDN’T REALISE YOU WERE A NONCE",
    "I HEARD YOU LIKE FINISHING EARLY",
    "JOIN THE QUANTUM BIOLOGY DISCORD SERVER! #GAMERSRISEUP",
    "WE SHOULD GET SOMETHING VENOMOUS LIKE A PLATYPUS",
    "THERE IS TOO MUCH ON YOUTUBE ABOUT PLATYPUS CUSTARD",
    "I DON'T BELIEVE IN GRANDCHILDREN",
    "WINNING IS NEVER AN OPTION, ONLY REVENGE",
    "FEDERICO’S ALLEYWAY BOUQUET",  # MW
    "SENT FROM MY GALAXY",
    "  _______\n /  12   \\ \n|    |    |\n|9   |   3|\n|     \\   |\n|         |\n \\___6___/\n\nGOOD HEAVENS, LOOK AT THE TIME!",
    # "Har🌳-Frick ✝️ ",
    "BRANEURISM\n\nSymptoms:\tlight-headed, delirium, dyslexic, autism, chicken sounds, flowcharts",
    f"       LISTEN TO PHAT BRAHMS\n        |                   \\\n        V                    \\\n    EAT KATSU                 \\     IS IT FRIDAY? ----> WAIT\n        |                      \\        | Yes  ^   No     |\n        V                       \\       V      L-----------\n    SPIN MESMERISING SPIN ORB   |   IS HILLSIDE OPEN? ---> KATSU\n        |                       |       |           \n        V                       ^       V            \n    [bold]BRANEURYSM[/bold]                  |   IS YOUNG'S OPEN ---> KATSU\n      /     \\                   |       |       \n     /YES    \\                  |       V\n    L         NO------->--------|   IS MAX IN THE OFFICE?\nKATSU COMA                      |       | Yes       \\ No\n                                ----<----            \\\n                                                    END THE DAY\n",
    "I WOULDN’T PAY £100 FOR A WET DREAM,\nFOR £100 I CAN GET A WET REALITY",
    "I KNOW YOUR FUTURE… BUT I’LL TELL YOU AFTER I GO TO THE LOO",
    "YOU ARE HEADING FOR A SMACK",
    "[bold]F*CK!!! WHY ARE THESE GUYS SUCH *$#@'S?![/bold]\n\n...\n\nI NEED ANOTHER COFFEE, I'M NOT ON EDGE ENOUGH.",  # MW
    "RESULTS ARE A SOCIAL CONSTRUCT",
    "AUTISOMANCY",
    "IS A HANGING MAN STANDING ON A BOX THAT HE IS HOLDING BENEATH HIS FEET A PERPETUAL MOTION MACHINE?",
    "HAVE YOU READ KARL MARX'S LATEST TWEET?",
    "WE NEED MORE GAY SCIENCE",
    "IF WE OVERCOME THIS I WILL JERK FROM NOW UNTIL THE NEXT YEAR",  # FB
    "DO LOOK A THIEVING STUFFED DOUGHNUT IN THE ASS",
    "YOU'RE NOT HUMAN UNTIL YOU'VE BEEN CITED",  # LS
    "TRUE [bold]AND[/bold] FALSE",
    "EINSTEIN? LARGELY A B*TCH",
    "I’M SCARED TO GO TO TEXAS, PEOPLE JUST SHOOTING ME",  # MS
    "YOU’RE WRONG WITH THAT, YOU’RE ABSOLUTELY WRONG WITH THAT",  # MS, supervisory meeting
    "WE SHOULD GET AN OFFICE DILDO",
    "AIDS SALIVA IS A-OK, SO YOU CAN GIVE THAT WHISTLE A SUCK",
    "NO ONE EVER SAID NOT TO EAT YELLOW RICE",
    "WALRUSES RAPING PENGUINS FOR REASONS THAT ARE NOT YET CLEAR",
    "THEY NEVER SAID DON'T EAT YELLOW RICE",
    "RUINING PEOPLE'S CAREERS BY KEEPING THEM IN THE SAME PLACE JUST BECAUSE I DID",  # JAK
    "WHEN I FIRST STARTED LECTURING I DID A LOT OF BUM WIGGLING",  # JAK
    "I DON'T UNDERSTAND HAVING VALUES",
    "PISS",
    "THAT'S THE ONLY REASON I'M NOT EATING YOUR FACE OFF RIGHT NOW",
    "DOUBLE-TEAMED BY GERIATRICS",
    "LIMPINGCHAN",
    "LET'S HAVE A QUICK CHAT? I NEED TO VENT SOME ANGER!",
    "THE FRENCHMAN BURNS EASILY",
    "WHY IS THE BROWN ALWAYS CAUSING PROBLEMS",
    "QUANTUM NATIONALISM",
    "THERE IS NO SUCH THING AS TIME",
    "IS OUR BANANA CORRECT?",
    "WOULD YOU RATHER:\n\nWALLACE HAMMERING FOR AN HOUR\n\nOR\n\nA BRIEF AL-QAEDA MOMENT?",
    "THE CONSPIRACY GROWS",
    "YOU'RE LOOKING GUILTIER BY THE SECOND",
    "I HAD TO MAKE SOMETHING, BUT I ONLY DESTROY",
    "QUANTUM CRY FOR HELP",
    "QB SOS",
    "UNFORUNATELY THE JAVA VERSION ON EUREKA IS TOO OLD TO RUN MINECRAFT",  # MW
    "NOBODY CARES, ESPECIALLY ME",
    "GEOGRAPHICALLY-CHALLENGED",
    "I GUESS THAT'S ONE GOOD THING ABOUT FASCISTS",
    "TESTICLES HAVE SO MUCH POTENTIAL",
    "WHENEVER IN DOUBT, GIVE LOUIE A SHOUT",
    "IF IN MOGADISHU, TELL LOUIE 'I MISS YOU'",
    "IF YOU'RE IN A PICKLE, GIVE LOUIE A TICKLE",
    "DOORS - UNLIKE PEOPLE - CAN BE UNFUCKED",  # MW
    "ARE YOU GOING TO GO TO HIS OFFICE, LIFT HIS ARMS UP AND GET YOUR FINGERS IN THERE?",
    "I CANNOT RIPEN MY OWN BANANA",
    "I DO BELIEVE!",
    "GREAT MINDS THINK THE SAME JUNK",
    """HI EVERYONE. HOW DO YOU KEEP WORKING WITH A COLLABORATOR IF YOUR LAST MEETING ENDED WITH YOU SAYING "SPARE ME THIS USELESS AND AGGRESSIVE RHETORIC, 'CAUSE I DON'T NEED IT, OR CARE ABOUT IT"?""",
    "LUCKILY SCIENCE AND DFT CALCULATIONS, DO NOT CARE ABOUT YOUR IMPRESSION OF THEM",  # FB
    "I WAS ONLY DOING AN IMPRESSION OF A NONCE!",
    "I GUESS WE ALL LEAVE AS FLESH",
    "SHOULD I BUY AN END OF LIFE PLANNER FOR MY PHD?",  # EN
    "WE NEED MORE MONEY TO MAKE STUDENTS SUFFER",
    "I WON'T TELL YOU WHAT TO DO, I'LL JUST JUDGE YOU",
    "NO, YOU DO NOT NEED TO STAY IN QB.\nAND YOU MIGHT NOT WANT TO DO SO",
    "SHIT CODE IS THE FIRST STEP TO NOT SHIT CODE",  # MW
    "GRANTS MAKE IT RAIN!",
    "YOU CAN'T GET DRUNK ON PISS",
    "CAN'T GET CANCELLED IF YOU'RE NOT FAMOUS",
    "I'M STARTING TO BELIEVE THESE ARE NOT REAL CONFUCIUS QUOTES",  # MS
    "WOULD YOU RATHER MAKE LOVE TO AN EYE OR A FOOT?",  # unknown @ MMC 2023
    "QUANTUM PHYSICS MEANS THAT ANYTHING CAN HAPPEN AT ANY TIME, FOR NO REASON",  # Futurama
    "I WOULD BE SCHLOBBIN ON SOMEONE'S KNOB FOR THAT",  # LS
    "THERE IS NO GREAT LOVE, WITHOUT GREAT JEALOUSY",  # Futurama
    "THE BAD BOYS WON'T WAIT ALL NIGHT",  # MW @ ABC 2023
    "YOU WON'T BELIEVE WHAT THIS OLD ITALIAN MAN PUT IN MY MIND",
    "THERE'S NOTHING NATURAL ABOUT AVERAGING COORDINATES",  # ABC 2023
    "ONIONS DON'T HURT ME",
    "THAT WAS BEFORE I DISCOVERED TURKISH MEN",  # RG @ ABC 2023
    "ALL COSTS ARE SUBSTANTIAL",
    "ALWAYS A GOOD IDEA TO BLAME THE FRENCH",
    "CHEESE, SEX AND ALIENS",  # about a museum in Basel
    "YOU HAVE TO ACCEPT YOUR MISERY",
    "COSTA RICA WAS A SIMULATION WITH THE WRONG FORCE FIELD",  # Leandro @ ABC 2023
    "LOW ENTROPY REGION OF NERDS",
    "THANK YOU FOR BEING WILLING",  # MW @ ABC 2023
    "HELLO STALKERS, COME TO ME",
    "YOU'RE ALWAYS ON THE RECEIVING END OF THE MOOSE SHAFTING",
    "IT'S A COCKTAIL OF SHIT",
    "F*CK HIM, CARVE YOUR OWN PATH",  # LS about Löwdin
    "I AM A STRAIGHT WHITE WHALE",
    "TO KILL A MONKEYBIRD",
    "LAZINESS LEADS TO THE ULTIMATE CREATIVITY",
    "DO YOU KNOW HOW TO READ [bold]FACIAL[/bold] LIPS?",
    "THERE'S TOO MANY BALD BASTARDS",
    "MAYBE YOU'RE THE D&D CHARACTER OF SOMEONE ELSE, AND THEY ARE DOING A REALLY BAD JOB",
    "THIS IS NOT AN ACT OF GOD, IT IS PITY",
    "FREUD'S THEORY ON GRAPEFRUITING YOUR DAD",
    "NORMALLY IT'S SHIT. BUT TODAY, IT'S [bold]EXCEPTIONALLY[/bold] SHIT",
    "WHAT ARE THESE REVOLUTIONARY LOOKING FIGURES? AH YES, HEXAGONS",
    "IF YOU ABUSE THEM, THEY'LL MOVE",
    "IT'S NOT SEXUAL HARASSMENT, IT'S A COMPLIMENT",
    "NOT A GOOD CRAZY",
    "EVENTUALLY YOU HAVE TO CARE ABOUT [bold]SOMETHING[/bold]",
    "DON'T PUSH THE RIVER",  # MW
    "THE DILDO OF CONSEQUENCES RARELY ARRIVES PRE-LUBED",  # REDDIT
    "IT'S ALL UNDER CONTROL",  # TH
    "THERE IS NO FUN WITHOUT VIOLENCE",  # GF
    "AN UBER IS TRANSIENT BUT SWIM TRUNKS ARE FOREVER",  # MW
    "IT'S NOT STEALING IF YOU PIONEER SOMETHING",  #  MW
    "THE SUFFERING IS OPTIONAL",
    "THAT'S THANKS TO LOUIE, AIMEE, AND - IT PAINS ME TO SAY IT - GEORGE",  # alex jones @ QuEBS 2023
    "HOME IS WHERE YOUR CHEEKS IMPRESS",  # MW
    "YOUR NUTS ARE DOING A REAL JOB ON MY THROAT",  # MW
    "VICIOUS CIRCLE OF BOLLOCKING",  # RL, XChem, Aug 2023
    "CROWDS GATHER TO WITNESS THE FIRST PANINI ARRIVE IN IRELAND",  # Waterford Whispers News
    "BLESSED ARE THE TOASTED SANDWICH MAKERS",  # Waterford Whispers News
    "BEEF JESUS DIED FOR OUR SINS",  # MW
    "I'M NOT IN A PICKLE, I'M IN A POTENTIAL WELL",
    "THE ELECTRON IDENTITY CRISIS",
    "TOY STORY IS A SOCIAL COMMENTARY ON THE MEASUREMENT PROBLEM",
    "DO YOU THINK SOME STUDENTS JUST AREN'T INTELLIGENT ENOUGH?",
    "YOU DON'T NEED A DEBUGGER. YOU NEED A PRIEST",  # MW
    "IF THE PAPER YOU WANT TO READ DOESN'T EXIST, WRITE IT",  # MW
    "THE WORLD IS YOUR HOSTAGE",  #
]

if __name__ == "__main__":
    app()