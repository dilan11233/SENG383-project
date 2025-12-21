package ui;

import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.util.List;
import java.util.function.Consumer;

import javax.swing.DefaultComboBoxModel;
import javax.swing.DefaultListModel;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextField;

import models.Task;
import utils.Validators;

public class TaskPanel extends JPanel {
    private final DefaultListModel<Task> listModel = new DefaultListModel<>();
    private final JList<Task> taskList = new JList<>(listModel);
    private final JComboBox<String> filterBox = new JComboBox<>();

    public TaskPanel(Consumer<Task> onAddTask, Consumer<String> onCompleteTask, Consumer<String> onFilterChanged) {
        setLayout(new BorderLayout());

        JPanel input = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JTextField titleField = new JTextField(10);
        JTextField descField = new JTextField(10);
        JComboBox<Task.Frequency> freqBox = new JComboBox<>(Task.Frequency.values());
        JTextField pointsField = new JTextField(5);
        JButton addBtn = new JButton("Add Task");

        input.add(new JLabel("Title"));
        input.add(titleField);
        input.add(new JLabel("Desc"));
        input.add(descField);
        input.add(new JLabel("Freq"));
        input.add(freqBox);
        input.add(new JLabel("Pts"));
        input.add(pointsField);
        input.add(addBtn);

        add(input, BorderLayout.NORTH);

        JPanel center = new JPanel(new BorderLayout());
        center.add(new JScrollPane(taskList), BorderLayout.CENTER);

        JPanel bottom = new JPanel(new FlowLayout(FlowLayout.LEFT));
        filterBox.setModel(new DefaultComboBoxModel<>(new String[]{"All", "Daily", "Weekly"}));
        JButton completeBtn = new JButton("Complete Selected");
        bottom.add(new JLabel("Filter"));
        bottom.add(filterBox);
        bottom.add(completeBtn);

        center.add(bottom, BorderLayout.SOUTH);
        add(center, BorderLayout.CENTER);

        addBtn.addActionListener(e -> {
            String title = titleField.getText();
            String desc = descField.getText();
            int pts = Validators.parsePositiveInt(pointsField.getText(), 5);
            Task task = new Task(title, desc, (Task.Frequency) freqBox.getSelectedItem(), pts);
            onAddTask.accept(task);
            titleField.setText("");
            descField.setText("");
            pointsField.setText("");
        });

        completeBtn.addActionListener(e -> {
            Task selected = taskList.getSelectedValue();
            if (selected != null) {
                onCompleteTask.accept(selected.getId());
            }
        });

        filterBox.addActionListener(e -> onFilterChanged.accept((String) filterBox.getSelectedItem()));
    }

    public void setTasks(List<Task> tasks) {
        listModel.clear();
        for (Task t : tasks) {
            listModel.addElement(t);
        }
        taskList.setCellRenderer((list, value, index, isSelected, cellHasFocus) -> {
            JLabel label = new JLabel(value.getTitle() + " (" + value.getFrequency() + ")" +
                    (value.isCompleted() ? " [done]" : ""));
            if (isSelected) {
                label.setOpaque(true);
                label.setBackground(list.getSelectionBackground());
                label.setForeground(list.getSelectionForeground());
            }
            return label;
        });
    }

    public String getSelectedFilter() {
        return (String) filterBox.getSelectedItem();
    }
}

