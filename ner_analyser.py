import nltk
from nltk import ne_chunk, pos_tag, word_tokenize, Tree
from pyspark.sql.functions import explode, split, col, lower, regexp_replace, udf, trim, to_json, struct

# NLTK modules downloads
nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")
nltk.download("maxent_ne_chunker")
nltk.download("words")


@udf()
def extract_named_entities(x):
    """
    Extract named entities from a sentence.
    :param x: sentence
    :return: list of entities
    """
    continuous_chunk = []
    current_chunk = []
    for i in ne_chunk(pos_tag(word_tokenize(x))):
        if type(i) is Tree:
            current_chunk.append(" ".join([token for token, pos in i.leaves()]))
        if current_chunk:
            named_entity = " ".join(current_chunk)
            if named_entity not in continuous_chunk and len(named_entity.split()) > 0:
                continuous_chunk.append(named_entity)
                current_chunk = []
        else:
            continue
    return continuous_chunk


def count_ner(articles):
    # Extract named entities and clean the text
    named_entities = (
        articles
        .select(extract_named_entities(col("text")).alias("value"))
        .withColumn('value', lower('value'))
        .withColumn("value", regexp_replace("value", r"[^ a-zA-Z0-9]+", ""))
    )

    # Generate word count
    output = (
        named_entities
        .select(
            explode(split(named_entities.value, ' '))
            .alias('word')
        )
        .withColumn("word", regexp_replace("word", r"^\s+$", ""))
        .filter(trim(col("word")) != "")
        .groupBy('word')
        .count()
        .select(to_json(struct(col("word"), col("count"))).alias("value"))
    )

    return output
