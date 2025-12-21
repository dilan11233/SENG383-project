package ui;

import java.awt.GridLayout;

import javax.swing.JLabel;
import javax.swing.JPanel;

import models.User;

public class ProgressPanel extends JPanel {
    private final JLabel pointsLabel = new JLabel("Points: 0");
    private final JLabel levelLabel = new JLabel("Level: 1");

    public ProgressPanel() {
        setLayout(new GridLayout(1, 2, 10, 0));
        add(pointsLabel);
        add(levelLabel);
    }

    public void update(User user) {
        pointsLabel.setText("Points: " + user.getPoints());
        levelLabel.setText("Level: " + user.getLevel());
    }
}


