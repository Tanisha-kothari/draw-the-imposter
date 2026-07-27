import random
from typing import Dict, List, Tuple

WordBankDict = Dict[str, Dict[str, List[str]]]

SEED_WORDS: WordBankDict = {
    "animals": {
        "easy": ["cat", "dog", "bird", "fish", "frog", "duck", "bear", "lion", "tiger", "horse",
                 "sheep", "pig", "cow", "rabbit", "mouse"],
        "medium": ["elephant", "giraffe", "dolphin", "penguin", "kangaroo", "octopus", "parrot",
                   "turtle", "shark", "eagle", "panda", "koala", "cheetah", "gorilla", "zebra"],
        "hard": ["chameleon", "platypus", "axolotl", "narwhal", "orangutan", "peacock",
                 "hedgehog", "flamingo", "caterpillar", "woodpecker", "salamander", "mongoose"],
    },
    "food": {
        "easy": ["pizza", "cake", "bread", "milk", "egg", "rice", "soup", "salad", "apple",
                 "banana", "grape", "lemon", "corn", "beans", "toast"],
        "medium": ["spaghetti", "hamburger", "sandwich", "omelette", "lasagna", "popcorn",
                   "cookies", "pancake", "waffle", "cupcake", "burrito", "bagel", "bacon"],
        "hard": ["croissant", "sashimi", "guacamole", "cappuccino", "wasabi", "caramel",
                 "mozzarella", "pistachio", "falafel", "hummus", "marmalade", "ravioli"],
    },
    "objects": {
        "easy": ["chair", "table", "book", "ball", "lamp", "clock", "door", "shoe", "hat",
                 "key", "bell", "rope", "comb", "soap", "coin"],
        "medium": ["umbrella", "backpack", "cushion", "candle", "mirror", "basket", "pillow",
                   "blanket", "bottle", "camera", "guitar", "ribbon", "bucket", "ladder"],
        "hard": ["binoculars", "microscope", "telescope", "barometer", "mannequin", "chandelier",
                 "megaphone", "kaleidoscope", "saxophone", "trampoline", "windmill"],
    },
    "activities": {
        "easy": ["run", "jump", "swim", "sing", "dance", "climb", "slide", "read", "draw",
                 "cook", "fish", "hike", "chase", "skate", "wave"],
        "medium": ["camping", "painting", "bowling", "sailing", "diving", "fencing", "hiking",
                   "juggling", "knitting", "sledding", "surfing", "cycling", "rowing"],
        "hard": ["paragliding", "sculpting", "calligraphy", "skydiving", "archery", "origami",
                 "bouldering", "snorkeling", "windsurfing", "blacksmith"],
    },
    "nature": {
        "easy": ["sun", "moon", "star", "tree", "rain", "snow", "wind", "lake", "hill",
                 "sand", "rock", "leaf", "seed", "wave", "ice"],
        "medium": ["mountain", "volcano", "waterfall", "rainbow", "lightning", "glacier",
                   "desert", "island", "canyon", "forest", "garden", "crystal", "meadow"],
        "hard": ["constellation", "biosphere", "earthquake", "mushroom", "stalactite",
                 "tornado", "lagoon", "taiga", "tundra", "mangrove", "geyser", "aurora"],
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

    def get_random_word(self, category: str | None = None, difficulty: str | None = None) -> Tuple[str, str, str]:
        """Pick a random word, optionally filtered by category and/or difficulty.

        Args:
            category: One of 'animals', 'food', 'objects', 'activities', 'nature', or None.
            difficulty: One of 'easy', 'medium', 'hard', or None.

        Returns:
            A tuple of (word, category, difficulty).

        Raises:
            ValueError: If the category or difficulty is invalid.
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

        if not pool:
            raise ValueError("No words found for the given filters.")

        word = random.choice(pool)
        selected_category = category or self._find_category(word)
        selected_difficulty = difficulty or self._find_difficulty(word)
        return word, selected_category, selected_difficulty

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
