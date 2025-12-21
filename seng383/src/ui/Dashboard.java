package ui;

import java.awt.BorderLayout;
import java.awt.GridLayout;
import java.util.List;

import javax.swing.JPanel;
import javax.swing.JTabbedPane;

import models.Task;
import models.User;
import models.Wish;

public class Dashboard extends JPanel {
    private final ProgressPanel progressPanel;
    private final TaskPanel taskPanel;
    private final WishPanel wishPanel;

    public Dashboard(ProgressPanel progressPanel,
                     TaskPanel taskPanel,
                     WishPanel wishPanel) {
        this.progressPanel = progressPanel;
        this.taskPanel = taskPanel;
        this.wishPanel = wishPanel;

        setLayout(new BorderLayout());
        add(progressPanel, BorderLayout.NORTH);

        JTabbedPane tabs = new JTabbedPane();
        tabs.addTab("Tasks", taskPanel);
        tabs.addTab("Wishes", wishPanel);

        add(tabs, BorderLayout.CENTER);
    }

    public void refresh(User user, List<Task> tasks, List<Wish> wishes) {
        progressPanel.update(user);
        taskPanel.setTasks(tasks);
        wishPanel.setWishes(wishes);
    }

    public String getTaskFilter() {
        return taskPanel.getSelectedFilter();
    }
}

