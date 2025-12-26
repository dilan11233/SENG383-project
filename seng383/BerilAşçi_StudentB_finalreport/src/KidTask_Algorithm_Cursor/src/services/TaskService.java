package services;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

import models.Task;
import models.User;
import repository.FileRepository;
import utils.ErrorHandler;

public class TaskService {
    private final FileRepository repo;
    private List<Task> tasks;

    public TaskService(FileRepository repo) {
        this.repo = repo;
        this.tasks = new ArrayList<>();
        load();
    }

    private void load() {
        this.tasks = repo.readAll("Tasks.txt", Task::fromStorageString);
        this.tasks.sort(Comparator.comparing(Task::getCreatedDate));
    }

    private void save() {
        repo.writeAll("Tasks.txt", tasks, Task::toStorageString);
    }

    public List<Task> getAll() {
        return new ArrayList<>(tasks);
    }

    public List<Task> getDailyTasks() {
        LocalDate today = LocalDate.now();
        return tasks.stream()
                .filter(t -> t.getFrequency() == Task.Frequency.DAILY)
                .filter(t -> !t.isCompleted() || t.getCreatedDate().isEqual(today))
                .collect(Collectors.toList());
    }

    public List<Task> getWeeklyTasks() {
        LocalDate startOfWeek = LocalDate.now().minusDays(LocalDate.now().getDayOfWeek().getValue() - 1);
        return tasks.stream()
                .filter(t -> t.getFrequency() == Task.Frequency.WEEKLY)
                .filter(t -> !t.isCompleted() || !t.getCreatedDate().isBefore(startOfWeek))
                .collect(Collectors.toList());
    }

    public void addTask(Task task) {
        tasks.add(task);
        save();
    }

    public boolean completeTask(String taskId, User user, LevelService levelService) {
        for (Task task : tasks) {
            if (task.getId().equals(taskId) && !task.isCompleted()) {
                task.markCompleted();
                user.addPoints(task.getPoints());
                levelService.updateLevel(user);
                save();
                return true;
            }
        }
        ErrorHandler.log("Task not found or already completed: " + taskId);
        return false;
    }
}

