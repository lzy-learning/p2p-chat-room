import logging
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QListWidget, \
    QPushButton, QDialog, QLabel, QLineEdit, QDialogButtonBox, QMessageBox
from PyQt5.QtWidgets import QPlainTextEdit, QCheckBox
from PyQt5.QtCore import pyqtSignal, QTimer
from controller import *
from utils import get_host_ip, if_ip_valid, if_port_valid, find_available_port, generate_content


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Login")
        self.setModal(True)

        self.ip_label = QLabel("IP:")
        self.ip_line = QLineEdit()
        self.ip_line.setText(get_host_ip())  # 默认 IP

        self.port_label = QLabel("Port:")
        self.port_line = QLineEdit()
        self.port_line.setText(f'{find_available_port(port_lb=10000)}')  # 找到第一个可用端口

        self.name_label = QLabel("Name:")
        self.name_line = QLineEdit()
        self.name_line.setText(get_name(self.ip_line.text(), int(self.port_line.text())))

        self.status_label = QLabel("")  # 用于显示验证状态的标签

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_line)
        layout.addWidget(self.ip_label)
        layout.addWidget(self.ip_line)
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_line)
        layout.addWidget(self.status_label)  # 显示验证状态的标签
        layout.addWidget(self.button_box)

    def validate_and_accept(self):
        name = self.name_line.text()
        ip = self.ip_line.text()
        port_text = self.port_line.text()

        if name is None:
            self.status_label.setText("Empty Name")
            return
        if if_ip_valid(ip) and if_port_valid(port_text):
            self.accept()
        else:
            self.status_label.setText("Invalid IP or Port")


class CreateGroupChatDialog(QDialog):
    def __init__(self, friends_list):
        super().__init__()

        self.friends_list = friends_list
        self.selected_friends = []
        self.group_chat_name = ""

        layout = QVBoxLayout()

        # 输入群聊名称
        name_label = QLabel("Group Name:")
        self.name_input = QLineEdit()
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        label = QLabel("Select friends to join the group chat")
        layout.addWidget(label)

        self.checkboxes = []

        for friend in self.friends_list:
            checkbox = QCheckBox(friend)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.confirm)
        layout.addWidget(confirm_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.setLayout(layout)
        self.setWindowTitle('Create new group')

    def confirm(self):
        # 获取用户输入的群聊名称
        self.group_chat_name = self.name_input.text()

        # 检查群聊名称是否为空
        if not self.group_chat_name:
            QMessageBox.warning(self, "Error", "Group name is invalid.")
        else:
            # 获取用户勾选的好友
            self.selected_friends = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]

            if not self.selected_friends:
                # 如果没有勾选好友，弹出提示
                QMessageBox.warning(self, "Error", "Group list can not be empty.")
            else:
                self.accept()


class JoinGroupChatDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.group_chat_name = ''
        layout = QVBoxLayout()

        # 输入群聊名称
        name_label = QLabel("Group Name:")
        self.name_input = QLineEdit()
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.confirm)
        layout.addWidget(confirm_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.setLayout(layout)
        self.setWindowTitle('Join a new group')

    def confirm(self):
        # 获取用户输入的群聊名称
        self.group_chat_name = self.name_input.text()

        # 检查群聊名称是否为空
        if not self.group_chat_name:
            QMessageBox.warning(self, "Error", "Group name is invalid.")
        else:
            # 调用服务端的加入群聊的接口
            if join_group(self.group_chat_name + '(Group)'):
                QMessageBox.information(self, 'success', f'Successfully join group {self.group_chat_name}')
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Can not find the group in current network")


class QuitGroupChatDialog(QDialog):
    def __init__(self, group_list):
        super().__init__()

        self.group_list = group_list
        self.selected_group = []

        layout = QVBoxLayout()

        label = QLabel("Select the groups you want to quit")
        layout.addWidget(label)

        self.checkboxes = []

        for group in self.group_list:
            checkbox = QCheckBox(group)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.confirm)
        layout.addWidget(confirm_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.setLayout(layout)
        self.setWindowTitle('Quit group')

    def confirm(self):
        # 获取用户勾选的好友
        self.selected_group = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]

        if not self.selected_group:
            QMessageBox.warning(self, "Error", "No group is selected")
        else:
            self.accept()


class ConnectDialog(QDialog):
    connection_established = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Connect")
        self.setModal(True)

        self.ip_label = QLabel("IP:")
        self.ip_line = QLineEdit()
        self.ip_line.setText(get_host_ip())

        self.port_label = QLabel("Port:")
        self.port_line = QLineEdit()
        self.port_line.setText('10000')

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.button_box.accepted.connect(self.accept_and_emit_signal)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.ip_label)
        layout.addWidget(self.ip_line)
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_line)
        layout.addWidget(self.button_box)

    def accept_and_emit_signal(self):
        ip = self.ip_line.text()
        port = int(self.port_line.text())
        self.connection_established.emit(ip, port)
        self.accept()


class ChatApp(QWidget):
    def __init__(self):
        super().__init__()

        # 登陆逻辑：选择本地服务器ip和port
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() != QDialog.Accepted:
            # 用户点击取消，关闭应用
            sys.exit()

        # 用户点击确认
        name = login_dialog.name_line.text()
        ip = login_dialog.ip_line.text()
        port = int(login_dialog.port_line.text())
        ChatApp.handle_login(name, ip, port)

        self.refresh_interval = 100

        # 好友列表
        self.friend_list = []
        self.current_friend = None
        self.friend_list_timer = QTimer(self)
        self.friend_list_timer.timeout.connect(self.update_friends_list)
        self.friend_list_timer.start(self.refresh_interval)

        self.friends_list_widget = QListWidget()
        self.friends_list_widget.addItems(self.friend_list)
        self.friends_list_widget.clicked.connect(self.on_friend_selected)  # 记录和谁在聊天

        # 消息展示列表
        self.message_display_k = 20
        self.message_display = QTextEdit()
        self.message_display_timer = QTimer(self)
        self.message_display_timer.timeout.connect(self.update_message_display)
        self.message_display_timer.start(self.refresh_interval)

        # 记录滚轮位置
        self.scroll_position = -1
        self.message_display.verticalScrollBar().valueChanged.connect(self.scrollbar_value_changed)

        self.message_display.setReadOnly(True)

        # 消息条数展示
        self.message_count_label = QLabel('', self)

        # 消息输入
        self.message_input = QPlainTextEdit()
        self.message_input.setPlaceholderText("Type your message and press Enter")
        self.message_input.setFixedHeight(80)  # Set the height to 80 pixels

        # self.message_input = QLineEdit()
        # self.message_input.setPlaceholderText("Type your message and press Enter")
        # self.message_input.setFixedHeight(80)

        # send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        # efficiency test button
        self.test_button = QPushButton("Test")
        self.test_button.clicked.connect(self.test)
        # connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.show_connect_dialog)
        # create group button
        self.create_group_chat_button = QPushButton("Create Group")
        self.create_group_chat_button.clicked.connect(self.create_group_chat)
        # join group button
        self.join_group_chat_button = QPushButton("Join Group")
        self.join_group_chat_button.clicked.connect(self.join_group_chat)
        # Quit group button
        self.quit_group_chat_button = QPushButton("Quit Group")
        self.quit_group_chat_button.clicked.connect(self.quit_group_chat)

        # Layout
        friend_layout = QVBoxLayout()
        friend_layout.addWidget(self.friends_list_widget)
        friend_layout.addWidget(self.connect_button)  # Connect button moved to the left
        friend_layout.addWidget(self.create_group_chat_button)
        friend_layout.addWidget(self.join_group_chat_button)
        friend_layout.addWidget(self.quit_group_chat_button)

        # message_layout = QVBoxLayout()
        # message_layout.addWidget(self.message_display)
        # message_layout.addWidget(self.message_input)
        #
        # button_layout = QVBoxLayout()  # Use QVBoxLayout for buttons on the right
        # button_layout.addWidget(self.send_button)
        # button_layout.addWidget(self.test_button)
        #
        # main_layout = QHBoxLayout(self)
        # main_layout.addLayout(friend_layout)
        # main_layout.addLayout(message_layout)
        # main_layout.addLayout(button_layout)

        right_layout = QVBoxLayout()

        message_display_layout = QVBoxLayout()
        message_display_layout.addWidget(self.message_display)

        message_input_send_layout = QHBoxLayout()
        message_input_layout = QVBoxLayout()
        message_input_layout.addWidget(self.message_input)
        message_send_layout = QVBoxLayout()
        message_send_layout.addWidget(self.send_button)
        message_send_layout.addWidget(self.test_button)
        message_input_send_layout.addLayout(message_input_layout)
        message_input_send_layout.addLayout(message_send_layout)

        right_layout.addLayout(message_display_layout)
        right_layout.addWidget(self.message_count_label)
        right_layout.addLayout(message_input_send_layout)

        main_layout = QHBoxLayout(self)
        main_layout.addLayout(friend_layout)
        main_layout.addLayout(right_layout)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 2)

        self.friends_list_widget.currentRowChanged.connect(self.display_chat)

        self.setWindowTitle(f"{name}'s Chat Room({ip}:{port})")
        self.setGeometry(100, 100, 800, 500)
        self.show()

    def update_friends_list(self):
        # 在这里调用后端接口获取最新好友列表，留下注释
        updated_friends_list = get_chat_list()

        # 如果好友列表发生变化，则更新前端显示
        if updated_friends_list != self.friend_list:
            self.friend_list = updated_friends_list
            self.friends_list_widget.clear()
            self.friends_list_widget.addItems(self.friend_list)
            if self.current_friend is not None and self.current_friend not in [self.friends_list_widget.item(i).text()
                                                                               for i in
                                                                               range(self.friends_list_widget.count())]:
                self.message_display.setPlainText('')

    def scrollbar_value_changed(self):
        self.scroll_position = self.message_display.verticalScrollBar().value()

    def scroll_to_position(self, position):
        self.message_display.verticalScrollBar().setValue(position)

    def update_message_display(self):
        if self.current_friend is None:
            return
        # 在这里调用后端接口获取与选中好友的聊天记录
        message_unit_list = get_chat_info(self.current_friend, self.message_display_k)

        self.message_display.verticalScrollBar().valueChanged.disconnect(self.scrollbar_value_changed)

        # 更新聊天记录显示
        if message_unit_list is None:
            self.message_display.setPlainText('')
        else:
            chat_history = [f'{message_unit.sender}: {message_unit.content}' for message_unit in message_unit_list]
            self.message_display.setPlainText('\n'.join(chat_history))
            if self.scroll_position != -1:
                self.scroll_to_position(self.scroll_position)
            else:
                cursor = self.message_display.textCursor()
                cursor.movePosition(cursor.End)
                self.message_display.setTextCursor(cursor)

        self.message_display.verticalScrollBar().valueChanged.connect(self.scrollbar_value_changed)

        if self.friends_list_widget.currentItem() is None:
            self.message_count_label.setText('')
        else:
            self.message_count_label.setText(
                f'Message count: {get_message_count(self.friends_list_widget.currentItem().text())}')

    def on_friend_selected(self):
        # 获取当前选中的好友
        selected_friend = self.friends_list_widget.currentItem()
        if selected_friend is None:
            return
        selected_friend = selected_friend.text()
        self.current_friend = selected_friend
        self.update_message_display()

    def create_group_chat(self):
        friend_list = list(filter(lambda friend: not friend.endswith('(Group)'), self.friend_list))
        create_group_chat_dialog = CreateGroupChatDialog(friend_list)
        result = create_group_chat_dialog.exec_()

        if result == QDialog.Accepted:
            # 用户点击确认，获取选择的好友列表
            selected_friends = create_group_chat_dialog.selected_friends
            group_chat_name = create_group_chat_dialog.group_chat_name

            if selected_friends:
                # 在这里调用后端接口创建群聊，后端会检查名称是否有效
                logging.info(f"Create Group: {group_chat_name}，members: {selected_friends}")
                if create_group(group_chat_name, selected_friends):
                    logging.info('create group successfully')
                else:
                    logging.error(f'failed to create group {group_chat_name}')
            else:
                # 用户未选择好友，弹出提示
                QMessageBox.warning(self, "Error", "Empty Group List!")

    def join_group_chat(self):
        join_group_chat_dialog = JoinGroupChatDialog()
        result = join_group_chat_dialog.exec_()

        if result == QDialog.Accepted:
            logging.info('Join group successfully.')
        else:
            logging.error('Can not join group.')

    def quit_group_chat(self):
        group_list = list(filter(lambda friend: friend.endswith('(Group)'), self.friend_list))
        quit_group_chat_dislog = QuitGroupChatDialog(group_list)
        result = quit_group_chat_dislog.exec_()

        if result == QDialog.Accepted:
            selected_groups = quit_group_chat_dislog.selected_group
            if not selected_groups:
                QMessageBox.warning(self, "Error", "Empty Group List!")
            for selected_group in selected_groups:
                if quit_group(selected_group):
                    logging.info(f'quit group {selected_group} successfully.')
                else:
                    logging.error(f'failed to quit group {selected_group}!')

    @staticmethod
    def handle_login(name, ip, port):
        # 在这里处理登录逻辑
        logging.info(f"Logged in with Name: {name}, IP: {ip}, Port: {port}")
        init(name, ip, port)

    def send_message(self):
        message = self.message_input.toPlainText()
        if message:
            selected_friend = self.friends_list_widget.currentItem().text()
            thread = threading.Thread(target=send_message, args=(selected_friend, message))
            thread.start()
            self.message_input.clear()

    def display_chat(self, index):
        selected_item = self.friends_list_widget.currentItem()
        if selected_item:
            chat_name = selected_item.text()
            self.message_display.clear()
            self.message_display.append(f"Chatting with {chat_name}")

    def show_connect_dialog(self):
        dialog = ConnectDialog(self)
        dialog.connection_established.connect(self.handle_connection)
        if dialog.exec_():
            ip = dialog.ip_line.text()
            port = dialog.port_line.text()
            self.message_display.append(f"Connected to {ip}:{port}")

    def handle_connection(self, ip, port):
        data = Data()
        if data.local_peer.ip == ip and data.local_peer.port == int(port):
            QMessageBox.critical(self, "Connection Status", f"can not connect to {ip}:{port}(yourself)")
            return
        logging.info(f'connecting to {ip}:{port}')
        # 在连接成功或失败时显示相应的信息
        ret_code = connect_peer_node(ip, int(port))
        if ret_code == 1:
            QMessageBox.information(self, "Connection Status", f"Successfully connected to {ip}:{port}")
            broadcast_my_existence()
        elif ret_code == -1:
            QMessageBox.information(
                self, "Connection Status", f"Failed to join the network.(Duplicate name: {data.local_peer.name})")
        else:
            QMessageBox.critical(self, "Connection Status", f"Failed to connect to {ip}:{port}. (Invalid address)")

    # 销毁服务器线程
    @staticmethod
    def clean_grpc_server():
        data = Data()
        data.server_thread.stop_server()
        data.server_thread.join()
        # 发送退出消息并保存当前数据
        normal_quit()

    # 测试
    def test(self):
        logging.info('testing......')

        def test_(friend):
            for _ in range(100):
                send_message(friend, generate_content())
                # time.sleep(1)

        selected_item = self.friends_list_widget.currentItem()
        if selected_item:
            chat_name = selected_item.text()
            thread = threading.Thread(target=test_, args=(chat_name,))
            thread.start()
        else:
            QMessageBox.critical(self, "Warnings", "You have to choose a chat first!")


if __name__ == '__main__':
    from local_data import Data

    app = QApplication(sys.argv)
    chat_app = ChatApp()
    app.aboutToQuit.connect(ChatApp.clean_grpc_server)
    sys.exit(app.exec_())
