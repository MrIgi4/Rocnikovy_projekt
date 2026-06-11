package org.example.ui;

import javafx.animation.PauseTransition;
import javafx.geometry.Insets;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.SplitPane;
import javafx.scene.control.ToolBar;
import javafx.scene.layout.*;
import javafx.stage.Popup;
import org.fxmisc.richtext.CodeArea;
import org.fxmisc.richtext.LineNumberFactory;
import org.fxmisc.richtext.event.MouseOverTextEvent;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;

public class MainController {

    private final BorderPane mainLayout;
    private CodeArea pythonEditor;
    private CodeArea cppEditor;
    private Button translateButton;
    private JSONArray documentationMap;

    public MainController() {
        mainLayout = new BorderPane();
        documentationMap = new JSONArray();
        initializeUI();
        initializeTooltip();
    }

    private void initializeUI() {
        pythonEditor = new CodeArea();
        // Adds line numbers
        pythonEditor.setParagraphGraphicFactory(LineNumberFactory.get(pythonEditor));
        pythonEditor.setPlaceholder(new javafx.scene.control.Label("Open a Python file or start writing to begin..."));

        cppEditor = new CodeArea();
        // Adds line numbers
        cppEditor.setParagraphGraphicFactory(LineNumberFactory.get(cppEditor));
        // Make the translation display read-only
        cppEditor.setEditable(false);


        SplitPane splitPane = new SplitPane();
        splitPane.getItems().addAll(pythonEditor, cppEditor);
        // 50% split
        splitPane.setDividerPositions(0.5);


        translateButton = new Button("Translate");
        translateButton.setOnAction(_ -> handleTranslation());

        ToolBar toolBar = new ToolBar(translateButton);
        mainLayout.setTop(toolBar);


        mainLayout.setCenter(splitPane);


        try {
            String cssPath = getClass().getResource("/theme.css").toExternalForm();
            mainLayout.getStylesheets().add(cssPath);
        } catch (NullPointerException e) {
            System.err.println("Could not find theme.css in resources path.");
        }
    }

    private void initializeTooltip(){
        Popup tooltipPopup = new Popup();
        VBox popupContent = new VBox();
        popupContent.setStyle("-fx-background-color: #2b2d30; " +
                "-fx-border-color: #4d4e51; " +
                "-fx-border-width: 1px; " +
                "-fx-padding: 8px; " +
                "-fx-background-radius: 4px; " +
                "-fx-border-radius: 4px;");

        Label tooltipLabel = new Label();
        tooltipLabel.setStyle("-fx-text-fill: #d4d4d4; -fx-font-family: 'Consolas';");
        popupContent.getChildren().add(tooltipLabel);
        tooltipPopup.getContent().add(popupContent);

        PauseTransition hideTimer = new PauseTransition(javafx.util.Duration.millis(200));
        hideTimer.setOnFinished(_ -> tooltipPopup.hide());

        cppEditor.setMouseOverTextDelay(java.time.Duration.ofMillis(400));

        cppEditor.addEventHandler(MouseOverTextEvent.MOUSE_OVER_TEXT_BEGIN, e -> {
            hideTimer.stop();

            int characterIndex = e.getCharacterIndex();
            String matchedDoc = null;

            for (int i = 0; i < documentationMap.length(); i++) {
                JSONObject range = documentationMap.getJSONObject(i);
                if (characterIndex >= range.getInt("start") && characterIndex <= range.getInt("end")) {
                    matchedDoc = range.getString("doc");
                    break;
                }
            }

            if (matchedDoc != null) {
                tooltipLabel.setText(matchedDoc);

                tooltipPopup.show(cppEditor, e.getScreenPosition().getX(), e.getScreenPosition().getY() + 5);
            }
        });

        cppEditor.addEventHandler(MouseOverTextEvent.MOUSE_OVER_TEXT_END, _ -> {
            hideTimer.playFromStart();
        });

        popupContent.setOnMouseEntered(_ -> {
            hideTimer.stop();
        });

        popupContent.setOnMouseExited(_ -> {
            hideTimer.playFromStart();
        });
    }

    private void handleTranslation() {
        String pythonCode = pythonEditor.getText();
        if (pythonCode.trim().isEmpty()) return;

        String rawJSON = runPythonTranspiler(pythonCode);

        try {
            JSONObject response = new JSONObject(rawJSON);

            String cppCode = response.getString("cpp_code");
            cppEditor.replaceText(cppCode);

            documentationMap = response.getJSONArray("documentation_list");

        } catch (Exception e) {
            // todo redirect to popup window instead
            cppEditor.replaceText("// Error parsing translation payload:\n" + rawJSON);
            documentationMap = new JSONArray();
        }
    }

    private String runPythonTranspiler(String pythonCode) {
        try {
            Path tempInputFile = Files.createTempFile("transpiler_input_", ".py");
            Files.writeString(tempInputFile, pythonCode);

            String pythonExePath = java.nio.file.Paths.get("python/.venv/Scripts/python.exe")
                    .toAbsolutePath()
                    .toString();

            ProcessBuilder pb = new ProcessBuilder(
                    pythonExePath,
                    "-m",
                    "java_bridge",
                    tempInputFile.toAbsolutePath().toString()
            );

            pb.directory(new java.io.File("python"));

            // todo redirect errors to window popup
            // Redirects errors to C++ code window
            pb.redirectErrorStream(true);

            Process process = pb.start();

            StringBuilder output = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append("\n");
                }
            }

            int exitCode = process.waitFor();

            Files.deleteIfExists(tempInputFile);

            if (exitCode != 0) {
                return "// ERROR: Python script crashed (Exit Code " + exitCode + "):\n" + output.toString();
            }

            return output.toString();

        } catch (Exception e) {
            e.printStackTrace();
            return "// ERROR: Failed to launch Python backend:\n" + e.getMessage();
        }
    }

    /**
     * Exposes the root view element so MainApp can mount it to the Scene.
     */
    public BorderPane getRootView() {
        return mainLayout;
    }
}