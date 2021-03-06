package clms.neam.classify;

import edu.stanford.nlp.ling.*;
import edu.stanford.nlp.ling.CoreAnnotations.*;
import edu.stanford.nlp.pipeline.*;
import edu.stanford.nlp.util.*;
import java.io.*;
import java.util.*;

/**
 * Named Entity/Automated Markup classifier: marks up documents with named entity tags.
 *
 * Initialize with a CoreNLP Properties object, then call classify on a file name to
 * classify that file.
 */
public class NEAMClassifier {

    /**
     * The CoreNLP pipeline to use to classify incoming text
     */
    private StanfordCoreNLP pipeline;

    /**
     * Map of Stanford tags to TEI tags
     */
    private Properties tags;

    /**
     * Initializes the classifier.
     *
     * @param props CoreNLP Properties to initialize the pipeline with
     * @param tags  
     */
    public NEAMClassifier(Properties props, Properties tags) {
        pipeline = new StanfordCoreNLP(props);
        this.tags = tags;
    }

    /**
     * Classifies a file.
     *
     * @param fileName The name of the file to classify
     * @return The text of the file, marked up with NE tags
     */
    public String classify(String text) {
        return classify(new Annotation(text));
    }

    public String classify(Annotation document) {
        pipeline.annotate(document);
        return tagDocument(document);
    }

    /**
     * Applies the annotations made to a document to the document itself.
     *
     * The document needs to have been already run through a pipeline.
     *
     * @param document The annotated document
     * @return The text of the document, with the named entites tagged in XML
     */
    private String tagDocument(Annotation document) {
        List<CoreMap> namedEntities = document.get(MentionsAnnotation.class);
        int lastPos = -1;
        int nextPos;
        String text = document.toString();
        String tag, phrase;
        StringBuilder builder = new StringBuilder();
        Collection<Object> acceptableTags = tags.values();

        for (CoreMap namedEntity : namedEntities) {
            tag = namedEntity.get(NamedEntityTagAnnotation.class);
            phrase = namedEntity.toString();

            if (tags.containsKey(tag)) {
                tag = tags.getProperty(tag);
            }

            // Find the location of the current phrase in the document
            nextPos = text.indexOf(phrase, lastPos);

            // For some reason, the annotator will tag things that aren't in the text
            // sometimes. This check makes sure that it really is tagging something
            // in the text.
            if (nextPos > 0) {
                // Append the text between the previous entity and the current entity
                builder.append(text.substring(lastPos + 1, nextPos));
                lastPos = nextPos + phrase.length() - 1;

                // Append the new named entity
                if (acceptableTags.contains(tag)) {
                    phrase = wrap(phrase, tag);
                }
                builder.append(phrase);
            }
        }

        // Add the stuff between the last NE and the end of the document
        builder.append(text.substring(lastPos + 1));

        return builder.toString();
    }

    /**
     * Wraps a string inside a set of tags.
     *
     * @param content The string to wrap
     * @param tag     The tag to wrap the content in
     * @return The content wrapped inside the tag
     */
    private String wrap(String content, String tag) {
        return String.format("<%s>%s</%s>", tag, content, tag);
    }
}

