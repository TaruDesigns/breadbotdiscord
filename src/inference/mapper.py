from loguru import logger

from settings import SETTINGS


class NoDetections(Exception): ...


class NoSegmentation(Exception): ...


class ResultsMapper:
    """Service that maps the results to a message"""

    @staticmethod
    def map_confidence_to_sentiment(confidence: float, label: str) -> str:
        # TODO: This is responsbility of the bot
        """Translate a confidence percentage to a text to indicate how accurate the element is

        Args:
            confidence (float): Confidence value
            label (str): Label for the confidence

        Returns:
            str: Value for the confidence specified
        """
        label = label.replace("_", " ")
        if confidence < 0.5:
            return f"{label}, H E L P, "
        elif confidence < 0.6:
            return f", just a bit {label}"
        elif confidence < 0.7:
            return f"reasonably {label}"
        elif confidence < 0.8:
            return f"probably {label}"
        elif confidence < 0.9:
            return f"fairly confident that it's {label}"
        elif confidence < 1.0:
            return f"pretty sure it is {label}"
        else:
            return f"Confirmed that it's {label}"

    @staticmethod
    def get_message_content_from_labels(
        predictions: dict[str, float], min_confidence: float | None = None
    ) -> str:
        # TODO: This is responsbility of the bot
        """Generate a message based on the input labels

        Args:
        labels (list[str], optional): Input labels. Defaults to None.

        Returns:
            str: Generated message to be used when sending
        """
        if min_confidence is None:
            min_confidence = SETTINGS.filter_bread_label_confidence
        labeltext = "This is certainly bread! "
        for label, confidence in predictions.items():
            if confidence >= min_confidence:
                labeltext = (
                    labeltext
                    + ResultsMapper.map_confidence_to_sentiment(
                        confidence=confidence, label=label
                    )
                    + " "
                )
        logger.debug(labeltext)
        return labeltext

    @staticmethod
    def get_message_from_roundness(roundness: float):
        if roundness is None:
            return "I don't think this bread is round at all..."
        messagecontent = f"This bread seems {round(roundness * 100, 2):.2f}% round. Anything over an 80% is pretty close to a sphere!"
        logger.debug(messagecontent)
        return messagecontent


if __name__ == "__main__":
    mapper = ResultsMapper()
