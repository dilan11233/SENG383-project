package ui;

import java.awt.BorderLayout;
import java.awt.CardLayout;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.SwingUtilities;

import models.Task;
import models.User;
import models.Wish;
import repository.FileRepository;
import services.LevelService;
import services.TaskService;
import services.WishService;
import utils.ErrorHandler;
import utils.Validators;

public class MainFrame extends JFrame {
    private final FileRepository repo = new FileRepository(Paths.get("data"));
    private final TaskService taskService = new TaskService(repo);
    private final WishService wishService = new WishService(repo);
    private final LevelService levelService = new LevelService();

    private final List<User> users = new ArrayList<>();
    private User currentUser;

    private final CardLayout cardLayout = new CardLayout();
    private final JPanel cards = new JPanel(cardLayout);

    private final ProgressPanel progressPanel = new ProgressPanel();
    private Dashboard dashboard;

    public MainFrame() {
        setTitle("KidTask");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(800, 600);
        setLocationRelativeTo(null);

        loadUsers();

        LoginScreen loginScreen = new LoginScreen(this::onLogin);
        cards.add(loginScreen, "login");

        add(cards, BorderLayout.CENTER);
    }

    private void ensureDashboard() {
        if (dashboard != null) {
            return;
        }
        TaskPanel taskPanel = new TaskPanel(this::addTask, this::completeTask, this::onFilterChanged);
        WishPanel wishPanel = new WishPanel(this::addWish, this::approveWish);
        dashboard = new Dashboard(progressPanel, taskPanel, wishPanel);
        cards.add(dashboard, "dashboard");
    }

    private void onLogin(String username, String password) {
        if (Validators.isNullOrEmpty(username) || Validators.isNullOrEmpty(password)) {
            ErrorHandler.show("Please enter username and password.");
            return;
        }
        Optional<User> existing = users.stream()
                .filter(u -> u.getUsername().equalsIgnoreCase(username))
                .findFirst();
        if (existing.isPresent()) {
            User user = existing.get();
            if (!user.getPassword().equals(password)) {
                ErrorHandler.show("Incorrect password.");
                return;
            }
            currentUser = user;
        } else {
            User user = new User(username, password);
            users.add(user);
            currentUser = user;
            saveUsers();
        }
        levelService.updateLevel(currentUser);
        ensureDashboard();
        refreshUI();
        cardLayout.show(cards, "dashboard");
    }

    private void addTask(Task task) {
        taskService.addTask(task);
        refreshUI();
    }

    private void completeTask(String taskId) {
        if (currentUser == null) {
            return;
        }
        if (taskService.completeTask(taskId, currentUser, levelService)) {
            saveUsers();
            refreshUI();
        }
    }

    private void addWish(Wish wish) {
        wishService.addWish(wish);
        refreshUI();
    }

    private void approveWish(String wishId) {
        if (currentUser == null) {
            return;
        }
        if (wishService.approveWish(wishId, currentUser)) {
            levelService.updateLevel(currentUser);
            saveUsers();
            refreshUI();
        }
    }

    private void onFilterChanged(String filter) {
        refreshUI();
    }

    private void refreshUI() {
        if (currentUser == null || dashboard == null) {
            return;
        }
        List<Task> tasksToShow;
        String filter = dashboard != null ? dashboard.getTaskFilter() : "All";
        switch (filter) {
            case "Daily":
                tasksToShow = taskService.getDailyTasks();
                break;
            case "Weekly":
                tasksToShow = taskService.getWeeklyTasks();
                break;
            default:
                tasksToShow = taskService.getAll();
                break;
        }
        dashboard.refresh(currentUser, tasksToShow, wishService.getAll());
    }

    private void loadUsers() {
        users.clear();
        users.addAll(repo.readAll("Users.txt", models.User::fromStorageString));
    }

    private void saveUsers() {
        repo.writeAll("Users.txt", users, models.User::toStorageString);
    }

    public static void launch() {
        SwingUtilities.invokeLater(() -> {
            MainFrame frame = new MainFrame();
            frame.setVisible(true);
        });
    }
}

