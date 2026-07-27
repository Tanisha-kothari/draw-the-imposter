import random
from typing import Dict, List, Set, Tuple

WordBankDict = Dict[str, Dict[str, List[str]]]

SEED_WORDS: WordBankDict = {
    "animals": {
        "easy": ["cat", "dog", "bird", "fish", "frog", "duck", "bear", "lion", "tiger", "horse",
                 "sheep", "pig", "cow", "rabbit", "mouse", "ant", "bee", "snail", "worm", "owl",
                 "bat", "seal", "fox", "wolf", "deer"],
        "medium": ["elephant", "giraffe", "dolphin", "penguin", "kangaroo", "octopus", "parrot",
                   "turtle", "shark", "eagle", "panda", "koala", "cheetah", "gorilla", "zebra",
                   "hamster", "raccoon", "beaver", "weasel", "badger"],
        "hard": ["chameleon", "platypus", "axolotl", "narwhal", "orangutan", "peacock",
                 "hedgehog", "flamingo", "caterpillar", "woodpecker", "salamander", "mongoose"],
    },
    "food": {
        "easy": ["pizza", "cake", "bread", "milk", "egg", "rice", "soup", "salad", "apple",
                 "banana", "grape", "lemon", "corn", "beans", "toast", "pear", "peach", "plum",
                 "melon", "kiwi", "mango", "cherry"],
        "medium": ["spaghetti", "hamburger", "sandwich", "omelette", "lasagna", "popcorn",
                   "cookies", "pancake", "waffle", "cupcake", "burrito", "bagel", "bacon",
                   "tortilla", "taco", "sushi", "donut", "muffin", "pretzel", "biscuit"],
        "hard": ["croissant", "sashimi", "guacamole", "cappuccino", "wasabi", "caramel",
                 "mozzarella", "pistachio", "falafel", "hummus", "marmalade", "ravioli",
                 "pomegranate", "artichoke"],
    },
    "objects": {
        "easy": ["chair", "table", "book", "ball", "lamp", "clock", "door", "shoe", "hat",
                 "key", "bell", "rope", "comb", "soap", "coin", "brush", "spoon", "fork",
                 "knife", "cup", "plate", "bowl", "bag"],
        "medium": ["umbrella", "backpack", "cushion", "candle", "mirror", "basket", "pillow",
                   "blanket", "bottle", "camera", "guitar", "ribbon", "bucket", "ladder",
                   "stapler", "scissors", "wallet", "suitcase", "hanger", "remote"],
        "hard": ["binoculars", "microscope", "telescope", "barometer", "mannequin", "chandelier",
                 "megaphone", "kaleidoscope", "saxophone", "trampoline", "windmill"],
    },
    "activities": {
        "easy": ["run", "jump", "swim", "sing", "dance", "climb", "slide", "read", "draw",
                 "cook", "fish", "hike", "chase", "skate", "wave", "skip", "hop", "crawl",
                 "throw", "catch", "kick", "build", "fly"],
        "medium": ["camping", "painting", "bowling", "sailing", "diving", "fencing", "hiking",
                   "juggling", "knitting", "sledding", "surfing", "cycling", "rowing",
                   "skateboarding", "snowboarding", "kayaking", "gardening", "yoga"],
        "hard": ["paragliding", "sculpting", "calligraphy", "skydiving", "archery", "origami",
                 "bouldering", "snorkeling", "windsurfing", "blacksmith"],
    },
    "nature": {
        "easy": ["sun", "moon", "star", "tree", "rain", "snow", "wind", "lake", "hill",
                 "sand", "rock", "leaf", "seed", "wave", "ice", "cloud", "river", "ocean",
                 "flower", "grass", "mud", "dust", "smoke"],
        "medium": ["mountain", "volcano", "waterfall", "rainbow", "lightning", "glacier",
                   "desert", "island", "canyon", "forest", "garden", "crystal", "meadow",
                   "peninsula", "plateau", "savanna", "monsoon", "blossom", "sunrise"],
        "hard": ["constellation", "biosphere", "earthquake", "mushroom", "stalactite",
                 "tornado", "lagoon", "taiga", "tundra", "mangrove", "geyser", "aurora"],
    },
    "sports": {
        "easy": ["soccer", "golf", "tennis", "baseball", "hockey", "boxing", "rugby",
                 "bowling", "cricket", "cycling", "skiing", "swimming", "running", "diving",
                 "yoga"],
        "medium": ["badminton", "basketball", "volleyball", "wrestling", "fencing", "karate",
                   "surfing", "archery", "skating", "snowboarding", "bobsled", "gymnastics",
                   "triathlon", "marathon", "kayaking", "polo"],
        "hard": [],
    },
    "movies": {
        "easy": ["popcorn", "ticket", "screen", "camera", "actor", "poster", "cinema",
                 "movie", "film", "star", "drama", "comedy", "scene", "story", "hero"],
        "medium": ["projector", "director", "script", "studio", "trailer", "sequel",
                   "premiere", "animation", "thriller", "musical", "fantasy", "western",
                   "horror", "documentary", "blockbuster", "episode"],
        "hard": [],
    },
    "countries": {
        "easy": ["India", "China", "Japan", "France", "Italy", "Spain", "Brazil", "Canada",
                 "Mexico", "Egypt", "Chile", "Peru", "Cuba", "Nepal", "Fiji"],
        "medium": ["Australia", "Germany", "Ireland", "Sweden", "Norway", "Poland", "Greece",
                   "Turkey", "Vietnam", "Thailand", "Morocco", "Kenya", "Colombia",
                   "Argentina", "Portugal", "Iceland"],
        "hard": [],
    },
    "cities": {
        "easy": ["Paris", "London", "Tokyo", "Dubai", "Rome", "Cairo", "Berlin", "Madrid",
                 "Moscow", "Delhi", "Sydney", "Seoul", "Lima", "Oslo", "Bali"],
        "medium": ["Shanghai", "Chicago", "Toronto", "Mumbai", "Istanbul", "Bangkok",
                   "Vienna", "Prague", "Dublin", "Munich", "Amsterdam", "Venice",
                   "Singapore", "Hong_Kong", "Auckland", "Barcelona"],
        "hard": [],
    },
    "professions": {
        "easy": ["doctor", "teacher", "nurse", "chef", "pilot", "farmer", "driver", "singer",
                 "dancer", "baker", "judge", "clerk", "guard", "tailor", "miner"],
        "medium": ["engineer", "lawyer", "dentist", "artist", "writer", "architect",
                   "scientist", "plumber", "electrician", "journalist", "photographer",
                   "musician", "surgeon", "mechanic", "firefighter", "astronaut"],
        "hard": [],
    },
    "vehicles": {
        "easy": ["car", "bus", "train", "boat", "bike", "truck", "plane", "ship", "jeep",
                 "van", "scooter", "wagon", "raft", "sled", "cart"],
        "medium": ["helicopter", "ambulance", "tractor", "subway", "rocket", "submarine",
                   "bicycle", "motorcycle", "sailboat", "kayak", "canoe", "glider",
                   "jetpack", "forklift", "carriage", "rickshaw"],
        "hard": [],
    },
    "instruments": {
        "easy": ["drum", "flute", "piano", "harp", "horn", "bell", "banjo", "organ",
                 "violin", "tuba", "lyre", "gong", "fife", "lute", "viola"],
        "medium": ["guitar", "trumpet", "cello", "clarinet", "ukulele", "accordion",
                   "harmonica", "mandolin", "maracas", "tambourine", "triangle",
                   "xylophone", "saxophone", "trombone", "keyboard", "bassoon"],
        "hard": [],
    },
    "technology": {
        "easy": ["phone", "radio", "clock", "lamp", "robot", "tablet", "mouse", "disk",
                 "chip", "screen", "cable", "drone", "flash", "server", "modem"],
        "medium": ["laptop", "printer", "camera", "scanner", "battery", "charger",
                   "keyboard", "monitor", "speaker", "console", "tracker", "android",
                   "browser", "network", "antenna", "satellite"],
        "hard": [],
    },
    "clothing": {
        "easy": ["shirt", "pants", "dress", "coat", "hat", "belt", "socks", "shoes",
                 "tie", "scarf", "glove", "vest", "boot", "cape", "mask"],
        "medium": ["jacket", "sweater", "trousers", "pajamas", "overalls", "sandals",
                   "sneakers", "necklace", "bracelet", "earring", "glasses", "goggles",
                   "helmet", "apron", "tuxedo", "kimono"],
        "hard": [],
    },
    "space": {
        "easy": ["star", "moon", "sun", "comet", "orbit", "rocket", "meter", "alien",
                 "laser", "cloud", "dust", "flag", "map", "lens", "beam"],
        "medium": ["planet", "galaxy", "eclipse", "capsule", "shuttle", "nebula",
                   "meteor", "crater", "gravity", "surface", "mission", "station",
                   "observatory", "telescope", "asteroid", "satellite"],
        "hard": [],
    },
    "cartoons": {
        "easy": ["robot", "castle", "wizard", "pirate", "knight", "ninja", "fairy",
                 "mermaid", "dragon", "giant", "alien", "clown", "magic", "hero", "ghost"],
        "medium": ["cartoon", "comic", "sketch", "anime", "manga", "puppet", "princess",
                   "superhero", "spaceship", "treasure", "monster", "unicorn", "dinosaur",
                   "vampire", "cactus", "sponge"],
        "hard": [],
    },
}

CATEGORIES = list(SEED_WORDS.keys())
DIFFICULTIES = ["easy", "medium", "hard"]


class WordBank:
    """Manages word selection organised by category and difficulty."""

    def __init__(self, words: WordBankDict | None = None) -> None:
        self._words = words or SEED_WORDS

    @property
    def words(self) -> WordBankDict:
        return self._words

    def get_random_word(
        self,
        category: str | None = None,
        difficulty: str | None = None,
        exclude: Set[str] | None = None,
    ) -> Tuple[str, str, str]:
        """Pick a random word, optionally filtered by category and/or difficulty.

        Args:
            category: Category name, or None for all categories.
            difficulty: One of 'easy', 'medium', 'hard', or None for all.
            exclude: Set of words to exclude (already used in this game).

        Returns:
            A tuple of (word, category, difficulty).

        Raises:
            ValueError: If no words match the given filters (after exclusions).
        """
        categories = [category] if category else CATEGORIES
        if category and category not in self._words:
            raise ValueError(f"Unknown category '{category}'. Options: {CATEGORIES}")

        difficulties = [difficulty] if difficulty else DIFFICULTIES
        if difficulty and difficulty not in DIFFICULTIES:
            raise ValueError(f"Unknown difficulty '{difficulty}'. Options: {DIFFICULTIES}")

        pool: List[str] = []
        for cat in categories:
            for diff in difficulties:
                pool.extend(self._words.get(cat, {}).get(diff, []))

        # Remove used words, but if the pool would be empty, allow reuse
        if exclude:
            available = [w for w in pool if w not in exclude]
            if available:
                pool = available

        if not pool:
            raise ValueError("No words found for the given filters.")

        word = random.choice(pool)
        selected_category = category or self._find_category(word)
        selected_difficulty = difficulty or self._find_difficulty(word)
        return word, selected_category, selected_difficulty

    def category_size(self, category: str) -> int:
        """Return the total number of unique words in a category."""
        if category not in self._words:
            return 0
        words = set()
        for diff_list in self._words[category].values():
            words.update(diff_list)
        return len(words)

    def total_words(self) -> int:
        """Return the total number of unique words across all categories."""
        all_words: set[str] = set()
        for cat in self._words.values():
            for diff_list in cat.values():
                all_words.update(diff_list)
        return len(all_words)

    def _find_category(self, word: str) -> str:
        for cat, diffs in self._words.items():
            for words_list in diffs.values():
                if word in words_list:
                    return cat
        return "unknown"

    def _find_difficulty(self, word: str) -> str:
        for diffs in self._words.values():
            for diff, words_list in diffs.items():
                if word in words_list:
                    return diff
        return "medium"


word_bank = WordBank()
