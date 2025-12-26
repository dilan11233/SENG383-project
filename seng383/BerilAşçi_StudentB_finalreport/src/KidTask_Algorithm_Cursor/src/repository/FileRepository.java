package repository;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

import utils.ErrorHandler;

public class FileRepository {
    private final Path dataDir;

    public FileRepository(Path dataDir) {
        this.dataDir = dataDir;
        ensureDir();
    }

    private void ensureDir() {
        try {
            Files.createDirectories(dataDir);
        } catch (IOException e) {
            ErrorHandler.log("Failed creating data directory: " + e.getMessage());
        }
    }

    public <T> List<T> readAll(String fileName, Function<String, T> mapper) {
        List<T> items = new ArrayList<>();
        Path filePath = dataDir.resolve(fileName);
        File file = filePath.toFile();
        if (!file.exists()) {
            return items;
        }
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = reader.readLine()) != null) {
                T obj = mapper.apply(line);
                if (obj != null) {
                    items.add(obj);
                } else {
                    ErrorHandler.log("Skipping corrupted line in " + fileName + ": " + line);
                }
            }
        } catch (IOException ex) {
            ErrorHandler.log("Error reading " + fileName + ": " + ex.getMessage());
        }
        return items;
    }

    public <T> void writeAll(String fileName, List<T> items, Function<T, String> serializer) {
        Path filePath = dataDir.resolve(fileName);
        ensureDir();
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(filePath.toFile()))) {
            for (T item : items) {
                writer.write(serializer.apply(item));
                writer.newLine();
            }
        } catch (IOException ex) {
            ErrorHandler.log("Error writing " + fileName + ": " + ex.getMessage());
        }
    }
}


