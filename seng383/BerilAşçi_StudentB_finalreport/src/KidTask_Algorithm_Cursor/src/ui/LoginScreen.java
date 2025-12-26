package ui;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.util.function.BiConsumer;

import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;

public class LoginScreen extends JPanel {
    private final JTextField usernameField = new JTextField(15);
    private final JPasswordField passwordField = new JPasswordField(15);

    public LoginScreen(BiConsumer<String, String> onLogin) {
        setLayout(new GridBagLayout());
        GridBagConstraints c = new GridBagConstraints();
        c.insets = new Insets(5, 5, 5, 5);
        c.fill = GridBagConstraints.HORIZONTAL;

        c.gridx = 0;
        c.gridy = 0;
        add(new JLabel("Username:"), c);

        c.gridx = 1;
        add(usernameField, c);

        c.gridx = 0;
        c.gridy = 1;
        add(new JLabel("Password:"), c);

        c.gridx = 1;
        add(passwordField, c);

        JButton loginBtn = new JButton("Login / Register");
        c.gridx = 0;
        c.gridy = 2;
        c.gridwidth = 2;
        add(loginBtn, c);

        loginBtn.addActionListener(e -> {
            String username = usernameField.getText();
            String password = new String(passwordField.getPassword());
            onLogin.accept(username, password);
        });
    }
}


