# applpine.py
#
# Copyright 2025 Alex-Build
#
# This Source Code Form is subject to the terms of the GPL
# License, v. 3.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.








# Libraries








import sys
import os
import re
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTPage, LTTextContainer, LTChar, LTTextLineHorizontal
import shutil
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QPushButton, QLabel, QProgressBar, QLineEdit, QGroupBox, QMenuBar, QDialog
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QAction, QPixmap
from typing import Match, Tuple, Union
from pathlib import Path








# Functionalities Class








class Functionalities(QThread):
    
    
    
    
    # Signals
    
    
    
    
    updateCreateBranchInternalLinksSignal : pyqtSignal = pyqtSignal(int)
    updateRenameBranchFilesFoldersSignal : pyqtSignal = pyqtSignal(int)
    updateRefreshBranchInternalLinksSignal : pyqtSignal = pyqtSignal(int)
    
    stopCreateBranchInternalLinksSignal : pyqtSignal = pyqtSignal()
    stopRenameBranchFilesFoldersSignal : pyqtSignal = pyqtSignal()
    stopRefreshBranchInternalLinksSignal : pyqtSignal = pyqtSignal()
    
    finished : pyqtSignal = pyqtSignal()
    stopped : pyqtSignal = pyqtSignal()




    # Constructor




    def __init__(self, absolute_branch_path : str, absolute_keywords_file_path : str, searching_word : str, replacing_word : str, refresh_branch_internal_links_bool : str):
        
        
        super().__init__()
        
        self.absolute_branch_path : str = absolute_branch_path
        self.absolute_keywords_file_path : str = absolute_keywords_file_path
        self.searching_word : str = searching_word
        self.replacing_word : str = replacing_word
        self.refresh_branch_internal_links_bool : str = refresh_branch_internal_links_bool
        self._stop : bool = False




    # Class Methods




    def get_waypoint_dict(self, absolute_branch_path : Path) -> dict[str, list[str]]:
        
        
        waypoint_dict : dict[str, list[str]] = {}


        def fill_waypoint_dict(absolute_branch_path : Path, parent_folder_name : str):
            
            
            item_name_list : list[str] = [item.name for item in absolute_branch_path.iterdir()]
            file_name_filtered_list : list[str] = [item_name for item_name in item_name_list if absolute_branch_path / item_name and item_name.endswith(".md") and str(os.path.splitext(item_name)[0]).lower() == parent_folder_name]
            file_path : str = ""
        
            for file_name_filtered in file_name_filtered_list:
                file_path = str(absolute_branch_path / file_name_filtered)
                if file_path not in waypoint_dict:
                    waypoint_dict[file_path] = [""]
        
            subfolder_name_filtered_list : list[str] = [item_name for item_name in item_name_list if (absolute_branch_path / item_name).is_dir()]
            subfolder_path : Path = Path("")
            child_file_path : str = ""
        
            for subfolder_name_filtered in subfolder_name_filtered_list:
                subfolder_path = absolute_branch_path / subfolder_name_filtered
                fill_waypoint_dict(subfolder_path, subfolder_path.name.lower())
            
                for file_name in [item.name for item in subfolder_path.iterdir()]:
                    child_file_path = str(absolute_branch_path / subfolder_name_filtered / file_name)
                    if file_path and child_file_path in waypoint_dict:
                        waypoint_dict[file_path].append(child_file_path)
    
    
        if absolute_branch_path and absolute_branch_path != Path("") and absolute_branch_path.is_dir():
    
            fill_waypoint_dict(absolute_branch_path, absolute_branch_path.name.lower())

            for waypoint_dict_key, waypoint_dict_value in waypoint_dict.items():
                for i in range(0, len(waypoint_dict_value)):
                    waypoint_dict[waypoint_dict_key][i] = Path(waypoint_dict[waypoint_dict_key][i]).parent.name

        return waypoint_dict




    def get_keyword_dict(self, absolute_keywords_file_path : Path) -> dict[str, str]:
    
    
        keyword_dict : dict[str, str] = {}
    
        if absolute_keywords_file_path and absolute_keywords_file_path != Path("") and absolute_keywords_file_path.is_file():
        
            absolute_keyword_folder_path : Path = absolute_keywords_file_path.parent
            item_name_list : list[str] = [item.name for item in absolute_keyword_folder_path.iterdir()]
            keyword_dict_key : str = ""
        
            for item_name in item_name_list:
                
                if item_name.endswith('.md') and str(os.path.splitext(item_name))[0] != absolute_keyword_folder_path.name:
                    keyword_dict_key = str(absolute_keyword_folder_path / item_name)
                    keyword_dict[keyword_dict_key] = str(os.path.splitext(item_name)[0])
                
            return keyword_dict
    
        else:
            return keyword_dict




    def create_branch_internal_links(self, waypoint_dict : dict[str, list[str]], keyword_dict : dict[str, str], absolute_keywords_file_path : Path):
        
        
        content : str = ""
        new_content : str = ""
        processed_files : int = 0
        total_files : int = len(list(waypoint_dict.keys())) + len(list(keyword_dict.keys()))

        if waypoint_dict:

            for waypoint_dict_key, waypoint_dict_value in waypoint_dict.items():
            
                if self._stop:
                    self.stopCreateBranchInternalLinksSignal.emit()
                    return
            
                with Path(waypoint_dict_key).open('r', encoding='utf-8') as f:
                    content = f.read()
                
                if "%% Hide %%" not in content:
                    
                    if "%% Begin Waypoint %%" not in content:
                        
                        if len(content) - len(content.rstrip("\n")) == 0:
                            new_content = content + "\n\n%% Begin Waypoint %%\n\n"
                        elif len(content) - len(content.rstrip("\n")) == 1:
                            new_content = content + "\n%% Begin Waypoint %%\n\n"
                        elif len(content) - len(content.rstrip("\n")) > 1:
                            new_content = content + "%% Begin Waypoint %%\n\n"
                        
                        for value in waypoint_dict_value:
                            if value:
                                new_content = new_content + "[[" + value + "]]\n\n"
                                
                        new_content = new_content + "%% End Waypoint %%"
                        
                        with Path(waypoint_dict_key).open('w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                processed_files += 1
                self.updateCreateBranchInternalLinksSignal.emit(int((processed_files / total_files) * 100))
            
        content = ""
        new_content = ""
            
        if keyword_dict and absolute_keywords_file_path and absolute_keywords_file_path != Path("") and absolute_keywords_file_path.is_file():
            
            with absolute_keywords_file_path.open('r', encoding='utf-8') as f:
                content = f.read()
        
            if len(content) - len(content.rstrip("\n")) == 0:
                new_content = "\n\n%% Begin Waypoint %%\n\n"
            elif len(content) - len(content.rstrip("\n")) == 1:
                new_content = "\n%% Begin Waypoint %%\n\n"
            elif len(content) - len(content.rstrip("\n")) > 1:
                new_content = "%% Begin Waypoint %%\n\n"
        
            for keyword_dict_key in keyword_dict.keys():
                
                if self._stop:
                    self.stopCreateBranchInternalLinksSignal.emit()
                    return
                
                new_content = new_content + "[[" + keyword_dict[keyword_dict_key] + "]]\n\n"
                processed_files += 1
                self.updateCreateBranchInternalLinksSignal.emit(int((processed_files / total_files) * 100))
        
            new_content = new_content + "%% End Waypoint %%"
        
            with absolute_keywords_file_path.open('w', encoding='utf-8') as f:
                f.write(new_content)




    def get_path_depth(self, path : str) -> int:
        
        
        return len(path.split(os.sep))




    def rename_files_folders(self, waypoint_dict : dict[str, list[str]]):
        
        
        absolute_md_file_paths_list : list[str] = list(waypoint_dict.keys())
        
        if absolute_md_file_paths_list != [""]:
        
            absolute_md_file_paths_list_sorted : list[str] = sorted(absolute_md_file_paths_list, key=self.get_path_depth, reverse=True)
            absolute_md_file_paths_list_sorted_filtered : list[Path] = [Path(item) for item in absolute_md_file_paths_list_sorted]
            folder_path : Path = Path("")
            file_path : str = ""
            new_file_path : Path = Path("")
            new_folder_path : Path = Path("")
            processed_files : int = 0
            total_files : int = len(absolute_md_file_paths_list_sorted_filtered)

            for absolute_md_file_path in absolute_md_file_paths_list_sorted_filtered:
                
                if self._stop:
                    self.stopRenameBranchFilesFoldersSignal.emit()
                    return
            
                folder_path, file_path = absolute_md_file_path.parent, absolute_md_file_path.name
                
                if absolute_md_file_path.is_file():
                    if str(os.path.splitext(file_path)[0]).lower() == self.searching_word.lower() and str(os.path.splitext(file_path)[1]).lower() == ".md":
                        new_file_path = folder_path / (folder_path.name + self.replacing_word + ".md")
                        absolute_md_file_path.rename(new_file_path)

                if folder_path.is_dir():
                    if folder_path.name.lower() == self.searching_word.lower():
                        new_folder_path = folder_path.parent / (folder_path.name + self.replacing_word)
                        if not new_folder_path.exists():
                            shutil.move(str(folder_path), str(new_folder_path))
        
                processed_files += 1
                self.updateRenameBranchFilesFoldersSignal.emit(int((processed_files / total_files) * 100))




    def refresh_branch_internal_links(self, waypoint_dict : dict[str, list[str]]):
    
    
        def delete_branch_internal_links(waypoint_dict : dict[str, list[str]]):
        
        
            total_files : int = len(list(waypoint_dict.keys()))
            lines : list[str] = []
            modified_lines : list[str] = []
            in_section : bool = False
            modification : bool = False
            processed_files : int = 0

            for waypoint_dict_key in waypoint_dict.keys():
            
                if self._stop:
                    self.stopRefreshBranchInternalLinksSignal.emit()
                    return
            
                with Path(waypoint_dict_key).open('r', encoding='utf-8') as f:
                    lines = f.readlines()
            
                modified_lines = []

                in_section = False
            
                modification = False

                for line in lines:
                    
                    if '%% Begin Waypoint %%' in line:
                        in_section = True
                        modification = True
                        continue
                    
                    elif '%% End Waypoint %%' in line and in_section:
                        in_section = False
                        continue
    
                    if not in_section:
                        modified_lines.append(line)

                if modification:
                    
                    with Path(waypoint_dict_key).open('w', encoding='utf-8') as f:
                        f.writelines(modified_lines)
            
                processed_files += 1
                self.updateRefreshBranchInternalLinksSignal.emit(int((processed_files / total_files) * 100))
    
    
        if waypoint_dict:
    
            delete_branch_internal_links(waypoint_dict)
    
            content : str = ""
            new_content : str = ""
            processed_files : int = 0
            total_files : int = len(list(waypoint_dict.keys()))

            for waypoint_dict_key, waypoint_dict_value in waypoint_dict.items():
            
                if self._stop:
                    self.stopRefreshBranchInternalLinksSignal.emit()
                    return
            
                with Path(waypoint_dict_key).open('r', encoding='utf-8') as f:
                    content = f.read()
                
                if "%% Hide %%" not in content:
                    
                    if "%% Begin Waypoint %%" not in content:
                        
                        if len(content) - len(content.rstrip("\n")) == 0:
                            new_content = content + "\n\n%% Begin Waypoint %%\n\n"
                        elif len(content) - len(content.rstrip("\n")) == 1:
                            new_content = content + "\n%% Begin Waypoint %%\n\n"
                        elif len(content) - len(content.rstrip("\n")) > 1:
                            new_content = content + "%% Begin Waypoint %%\n\n"
                        
                        for value in waypoint_dict_value:
                            if value:
                                new_content = new_content + "[[" + value + "]]\n\n"
                                
                        new_content = new_content + "%% End Waypoint %%"
                        
                        with Path(waypoint_dict_key).open('w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                processed_files += 1
                self.updateRefreshBranchInternalLinksSignal.emit(int((processed_files / total_files) * 100))




    def run(self):
        
        
        if os.name == 'nt':
            if self.absolute_branch_path.startswith("file:///"):
                self.absolute_branch_path = self.absolute_branch_path[len("file:///"):]

            self.absolute_branch_path = os.fsencode(os.path.normpath("\\\\?\\" + os.path.abspath(self.absolute_branch_path)).replace('\\', '/').replace('"', '')).decode("utf-8")
            
            if self.absolute_keywords_file_path:
                if self.absolute_keywords_file_path.startswith("file:///"):
                    self.absolute_keywords_file_path = self.absolute_keywords_file_path[len("file:///"):]
                self.absolute_keywords_file_path = os.fsencode(os.path.normpath("\\\\?\\" + os.path.abspath(self.absolute_keywords_file_path)).replace('\\', '/').replace('"', '')).decode("utf-8")
        else:
            if self.absolute_branch_path.startswith("file://"):
                self.absolute_branch_path = self.absolute_branch_path[len("file://"):]
            if self.absolute_keywords_file_path.startswith("file://"):
                self.absolute_keywords_file_path = self.absolute_keywords_file_path[len("file://"):]
                    
            self.absolute_branch_path = os.path.normpath(self.absolute_branch_path).replace('\\', '/').replace('"', '')
            self.absolute_keywords_file_path = os.path.normpath(self.absolute_keywords_file_path).replace('\\', '/').replace('"', '')
        
        if self.absolute_branch_path and self.absolute_branch_path != ".":
        
            if self.searching_word and self.replacing_word:
                
                absolute_branch_path : Path = Path(self.absolute_branch_path)
                
                if absolute_branch_path.is_dir():
                    waypoint_dict : dict[str, list[str]] = self.get_waypoint_dict(absolute_branch_path)
                    if waypoint_dict:
                        self.rename_files_folders(waypoint_dict)    
            
            elif self.refresh_branch_internal_links_bool == "true":
                
                absolute_branch_path : Path = Path(self.absolute_branch_path)
                
                if absolute_branch_path.is_dir():
                    waypoint_dict : dict[str, list[str]] = self.get_waypoint_dict(absolute_branch_path)
                
                    if waypoint_dict:
                        self.refresh_branch_internal_links(waypoint_dict)
            
            else:
                
                if self.absolute_keywords_file_path and self.absolute_keywords_file_path != ".":
                    
                    absolute_keywords_file_path : Path = Path(self.absolute_keywords_file_path)
                    
                    if absolute_keywords_file_path.is_file():
                    
                        keyword_dict : dict[str, str] = self.get_keyword_dict(absolute_keywords_file_path)
                    
                        if keyword_dict:
                    
                            absolute_branch_path : Path = Path(self.absolute_branch_path)
                
                            if absolute_branch_path.is_dir():
                            
                                waypoint_dict : dict[str, list[str]] = self.get_waypoint_dict(absolute_branch_path)
                    
                                if waypoint_dict:
                        
                                    self.create_branch_internal_links(waypoint_dict, keyword_dict, absolute_keywords_file_path)
                    
                else:
                    
                    absolute_branch_path : Path = Path(self.absolute_branch_path)
                
                    if absolute_branch_path.is_dir():
                        
                        waypoint_dict : dict[str, list[str]] = self.get_waypoint_dict(absolute_branch_path)
                        absolute_keywords_file_path : Path = Path("")
                        keyword_dict : dict[str, str] = {}
                
                        if waypoint_dict:

                            self.create_branch_internal_links(waypoint_dict, keyword_dict, absolute_keywords_file_path)    

            self.finished.emit()




    def stop(self):
        
        
        self._stop = True




    # Class Static Methods




    @staticmethod
    def extract_text_from_pdf(absolute_input_file_path : Path)->str:


        all_content : str = ""
    
        if absolute_input_file_path and absolute_input_file_path != Path("") and absolute_input_file_path.is_file():
    
            try:
    
                for page_layout in extract_pages(absolute_input_file_path):
                    all_content += Functionalities.add_whitespace_to_text(page_layout)
            
            except Exception:
                
                return ""
    
        return all_content




    @staticmethod
    def add_whitespace_to_text(page_layout : LTPage)->str:


        x_first_char_pos : float = 0.0
        y_last_line_position : float = 0.0
        vertical_difference : float = 0.0
        ligne_height : int = 15
        empty_line_total : int = 0
        page_text : str = ""
        tab_counter : int = 0
        tab : str = ""
        
        for element in page_layout:
            
            if isinstance(element, LTTextContainer):
                
                for line in element:
                    
                    if isinstance(line, LTTextLineHorizontal):
                        
                        x_first_char_pos = 0
                        
                        if len(line._objs) > 0 and isinstance(line._objs[0], LTChar):
                            x_first_char_pos = line._objs[0].x0
                        
                        if y_last_line_position > 0:
                            vertical_difference = float(abs(y_last_line_position - line.y0))
                            
                            if vertical_difference > ligne_height:
                                
                                empty_line_total = int(vertical_difference // ligne_height)
                                page_text += "\n" * empty_line_total
                        
                        tab_counter = int(x_first_char_pos // 40) - 1
                        tab = "\t" * (tab_counter)
                        page_text += tab + line.get_text().strip() + "\n"
                        y_last_line_position = line.y0
        
        return page_text




    @staticmethod
    def create_configuration_file_content(input_file_content: str) -> str:
    
    
        if input_file_content:
    
            input_file_lines : list[str] = input_file_content.splitlines()
            match_title : (Match[str] | None) = None
            current_title : str = ""
            input_file_text_by_title_dict : dict[str, str] = {}
            current_text_list : list[str] = []
            level_title : str = ""
            text_title : str = ""
            input_file_title_list : list[Tuple[str, str]] = []
    
            for input_file_line in input_file_lines:
                
                match_title = re.match(r"^\s*(\d+(\s*\.\s*\d+)*)(\s*&\s*)(.*)", input_file_line)
        
                if match_title:
            
                    if current_title and current_title not in list(input_file_text_by_title_dict.keys()):
                        input_file_text_by_title_dict[current_title] = "\n".join(current_text_list)
            
                    level_title = match_title.group(1).strip()
                    text_title = match_title.group(4).strip()
                    
                    if text_title:
                        input_file_title_list.append((level_title, text_title))
                        current_title = text_title
                    
                    current_text_list = []
            
                elif current_title and current_title not in list(input_file_text_by_title_dict.keys()): 
                    current_text_list.append(input_file_line)
    
            if current_title and current_title not in list(input_file_text_by_title_dict.keys()):
                input_file_text_by_title_dict[current_title] = "\n".join(current_text_list)

            level : int = 0
            result : list[str] = []
    
            for level_title, text_title in input_file_title_list:
                
                level = level_title.count('.') + 1 
        
                if text_title in input_file_text_by_title_dict and input_file_text_by_title_dict[text_title]:
                    result.append(f"{'*' * level}{text_title} (X)")
                else:
                    result.append(f"{'*' * level}{text_title}")
    
            result.append("")
            
            sorted_title_list : list[str] = []
    
            for level_title, text_title in input_file_title_list:
                
                if text_title in input_file_text_by_title_dict and input_file_text_by_title_dict[text_title] and text_title not in sorted_title_list:
                    result.append(f"{text_title} (X)")
                    result.append("&")
                    result.append(input_file_text_by_title_dict[text_title])
                    result.append("&")
                    result.append("")
                    sorted_title_list.append(text_title)

            return "\n".join(result)
        
        else:
            return ""




    @staticmethod
    def save_configuration_file(absolute_input_file_path : Path, configuration_file_content: str):
    
    
        if absolute_input_file_path and absolute_input_file_path != Path("") and absolute_input_file_path.is_file() and configuration_file_content:
        
            configuration_file_path : Path = absolute_input_file_path.parent / ("Configuration File - " + absolute_input_file_path.stem.lower().title() + ".txt")

            if configuration_file_path:
                    
                with configuration_file_path.open('w', encoding='utf-8') as f:
                    f.write(configuration_file_content)




    @staticmethod
    def create_configuration_file(absolute_input_file_path : Union[str, Path]):
        
        
        if os.name == 'nt':
            if absolute_input_file_path.startswith("file:///"):
                absolute_input_file_path = absolute_input_file_path[len("file:///"):]

            absolute_input_file_path = Path(os.fsencode(os.path.normpath("\\\\?\\" + os.path.abspath(absolute_input_file_path)).replace('\\', '/').replace('"', '')).decode("utf-8"))
        else:
            if absolute_input_file_path.startswith("file://"):
                absolute_input_file_path = absolute_input_file_path[len("file://"):]
                    
            absolute_input_file_path = Path(os.path.normpath(absolute_input_file_path).replace('\\', '/').replace('"', ''))
        
        if absolute_input_file_path and absolute_input_file_path != Path("") and absolute_input_file_path.is_file():
                
            input_file_content : str = Functionalities.extract_text_from_pdf(absolute_input_file_path)
            configuration_file_content : str = Functionalities.create_configuration_file_content(input_file_content)
            Functionalities.save_configuration_file(absolute_input_file_path, configuration_file_content)




    @staticmethod
    def find_folder_path_with_parent(path : Path, folder_name : str) -> Path:
        
        
        if path and path != Path("") and path.is_dir() and folder_name:
        
            path_list : list[Path] = [path]
            root : Path = Path("")
            item_name_list : list[str] = []
            folder_name_list : list[str] = []
            folder_path : Path = Path("")
            
            while path_list:
                
                root = path_list.pop(0)
                item_name_list = [item.name for item in root.iterdir()]
                
                try:
                    
                    folder_name_list = []
                    
                    for folder in item_name_list:
                        
                        if (root / folder).is_dir():
                            if not folder.startswith('.'):
                                folder_name_list.append(folder)
                                path_list.append(root / folder)
                                
                    if folder_name in folder_name_list:
                        folder_path = root / folder_name
                        
                except PermissionError:
                    
                    folder_path = Path("")
                    
                except FileNotFoundError:
                    
                    folder_path = Path("")
                
            return folder_path
        
        else:
            return Path("")




    @staticmethod
    def create_branch(absolute_configuration_file_path : Union[str, Path], absolute_branch_path : Union[str, Path], absolute_parent_folder_path : Union[str, Path], keywords_bool: str):
        
        
        if os.name == 'nt':
            if absolute_configuration_file_path.startswith("file:///"):
                absolute_configuration_file_path = absolute_configuration_file_path[len("file:///"):]
            if absolute_branch_path.startswith("file:///"):
                absolute_branch_path = absolute_branch_path[len("file:///"):]
            if absolute_parent_folder_path.startswith("file:///"):
                absolute_parent_folder_path = absolute_parent_folder_path[len("file:///"):]

            absolute_configuration_file_path = Path(os.fsencode(os.path.normpath("\\\\?\\" + os.path.abspath(absolute_configuration_file_path)).replace('\\', '/').replace('"', '')).decode("utf-8"))
            absolute_branch_path = Path(os.fsencode(os.path.normpath("\\\\?\\" + os.path.abspath(absolute_branch_path)).replace('\\', '/').replace('"', '')).decode("utf-8"))
            absolute_parent_folder_path = Path(os.fsencode(os.path.normpath("\\\\?\\" + os.path.abspath(absolute_parent_folder_path)).replace('\\', '/').replace('"', '')).decode("utf-8"))
        else:
            if absolute_configuration_file_path.startswith("file://"):
                absolute_configuration_file_path = absolute_configuration_file_path[len("file://"):]
            if absolute_branch_path.startswith("file://"):
                absolute_branch_path = absolute_branch_path[len("file://"):]
            if absolute_parent_folder_path.startswith("file://"):
                absolute_parent_folder_path = absolute_parent_folder_path[len("file://"):]
        
            absolute_configuration_file_path = Path(os.path.normpath(absolute_configuration_file_path).replace('\\', '/').replace('"', ''))
            absolute_branch_path = Path(os.path.normpath(absolute_branch_path).replace('\\', '/').replace('"', ''))
            absolute_parent_folder_path = Path(os.path.normpath(absolute_parent_folder_path).replace('\\', '/').replace('"', ''))
        
        if absolute_configuration_file_path and absolute_configuration_file_path != Path("") and absolute_branch_path and absolute_branch_path != Path("") and absolute_configuration_file_path.is_file() and absolute_branch_path.is_dir():
                
            lines : list[str] = []
                
            with absolute_configuration_file_path.open('r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if lines:
                
                if keywords_bool == "true":
                    if absolute_parent_folder_path and absolute_parent_folder_path != Path("") and absolute_parent_folder_path.is_dir():
                        keyword_path : Path = Functionalities.find_folder_path_with_parent(absolute_parent_folder_path, "Keywords")
                else:
                    keyword_path : Path = Path("")
                    
                current_path : Path = absolute_branch_path
                branch_counter : int = 0
                level : int = 0
                keyword_list : list[str] = []
                keyword_path_list : list[Path] = []
                path_list : list[Path] = []
                folder_name : str = ""
                stack : list[Path] = []
                content_dict : dict[Path, str] = {}
                content_lines : list[str] = []
                processing_content : bool = False
                md_file_path : Path = Path("")
                content : str = ""
                content_keyword_dict : dict[Path, str] = {}
                matching_key : Path = None
                current_title : str = ""
                
                for line in lines:
                        
                    if branch_counter < 2:
                        
                        line = line.strip()
                        
                        if line.startswith('*'):
                            
                            level = line.count('*')
                                
                            if "Keywords" in line:
                                    
                                if keyword_path and keyword_path != Path("") and bool(re.match(r'^Keywords \[([\w\s]+(, [\w\s]+)*)?\]$', line.strip("*").strip())) == True:
                                    keyword_list = line.strip("*").strip().split('[')[1].strip(']').split(', ')
                                    keyword_path_list = [keyword_path / (keyword + ".md") for keyword in keyword_list]
                                    if keyword_path_list:
                                        for keywords_path in keyword_path_list:
                                            if not keywords_path.exists():
                                                path_list.append(keywords_path)
                                        folder_name = line.strip('*').strip().split(' [')[0]
                                    else:
                                        folder_name = ""
                                else:
                                    folder_name = ""
                            else:
                                folder_name = line.strip('*').strip()
                            
                            if folder_name:
                                    
                                if level == 1:
                                        
                                    branch_counter += 1
                                    current_path = absolute_branch_path / (folder_name)
                                        
                                else:
                                        
                                    while len(stack) >= level:
                                        stack.pop()
                                            
                                    if stack:
                                        current_path = stack[-1] / (folder_name)
                                    else:
                                        current_path = absolute_branch_path / (folder_name)
                            
                                if not current_path.exists():
                                    current_path.mkdir(parents=True, exist_ok=True)
                            
                                stack = stack[:level-1] + [current_path]
                            
                                content_dict[current_path] = ''
                                content_lines = []
                                processing_content = False
                            
                                if "Keywords" in line and keyword_path and keyword_path != Path("") and bool(re.match(r'^Keywords \[([\w\s]+(, [\w\s]+)*)?\]$', line.strip("*").strip())) == True:
                                    keyword_list = line.strip("*").strip().split('[')[1].strip(']').split(', ')                
                                    md_file_path = current_path / (current_path.name + ".md")
                                    content = ""
                                    for keyword in keyword_list:
                                        content += "[[" + keyword + "]]\n"
                                    content_keyword_dict[md_file_path] = content
                        
                        elif line == '&':
                            
                            if processing_content:
                                matching_key = next((key for key in content_dict if current_title == str(key).replace("\\", "/").split('/')[-1]), None)
                                if matching_key:
                                    content_dict[matching_key] = '\n'.join(content_lines) + '\n'
                                content_lines = []
                                processing_content = False
                                
                            else:
                                processing_content = True
                    
                        else:
                            
                            if processing_content:
                                content_lines.append(line)
                            else:
                                current_title = line
                                    
                    else:
                        return
                
                md_file_path = Path("")
                    
                for folder_path, content in content_dict.items():
                    md_file_path = folder_path / (folder_path.name + ".md")
                    with md_file_path.open('w', encoding='utf-8') as f:
                        f.write("\n" + content)
                
                for path in path_list:
                    with path.open('w', encoding='utf-8') as f:
                        f.write("")
                
                for md_file_path, content in content_keyword_dict.items():
                    with md_file_path.open('w', encoding='utf-8') as f:
                        f.write(content)








# Application








class App(QWidget):
    
    
    
    
    # Constructor
    
    
    
    
    def __init__(self):
        
        
        super().__init__()
        
        self.initUI()




    # Class Methods




    def initUI(self):
        
        
        self.setWindowTitle("AppLPine 1.0")
        self.setWindowIcon(QIcon(os.getcwd() + "/Icon.png"))
        self.setMinimumSize(int(QApplication.primaryScreen().availableGeometry().width() * 0.25), int(QApplication.primaryScreen().availableGeometry().height() * 0.25))
        self.resize(int(QApplication.primaryScreen().availableGeometry().width() * 0.25), int(QApplication.primaryScreen().availableGeometry().height() * 0.75))
        self.setStyleSheet("background-color: rgb(116, 96, 69); font-size: 16px; color: rgb(206, 180, 146)")


        mainLayout = QHBoxLayout()

        mainMenuBar = QMenuBar(self)
        mainLayout.setMenuBar(mainMenuBar)
        
        helpMainMenu = mainMenuBar.addMenu("Help")
        helpMainAction = QAction("Help", self)
        helpMainAction.triggered.connect(self.showHelpDialog)
        helpMainMenu.addAction(helpMainAction)
        
        aboutMainMenu = mainMenuBar.addMenu("About")
        aboutMainAction = QAction("About", self)
        aboutMainAction.triggered.connect(self.showAboutDialog)
        aboutMainMenu.addAction(aboutMainAction)

        mainPixmap = QPixmap(os.getcwd() + "/Icon.png")
        
        mainLabel = QLabel(self)
        mainLabel.setPixmap(mainPixmap.scaledToWidth(50, Qt.TransformationMode.SmoothTransformation))
        mainLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        mainLayout.addWidget(mainLabel)


        self.functionalitiesScrollArea = QScrollArea(self)
        self.functionalitiesScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.functionalitiesScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.functionalitiesScrollArea.setWidgetResizable(True)

        self.functionalitiesGroupbox = QGroupBox(self)

        functionalitiesLayout = QVBoxLayout()


        self.createConfigurationFileGroupbox = QGroupBox("Create Configuration File", self)
        
        createConfigurationFileLayout = QVBoxLayout()

        self.createConfigurationFileInputFileInput = QLineEdit(self)
        self.createConfigurationFileInputFileInput.setPlaceholderText('Enter PDF File Absolute Path')
        self.createConfigurationFileInputFileInput.setToolTip('(Add ".pdf" Extension File)\n\n(To Create Text Configuration File Which Will Create Branch)\n\n(IMPORTANT : Please, avoid "&" in the PDF file content. "&" can only be inserted as a separator just after a title level in the PDF file.)\n\n(IMPORTANT : To create the branch, the PDF file must contains at most one single level 1 title.)\n\n(IMPORTANT : Please, avoid writing the exact same following sentences in the PDF file content : "%% Hide %%" OR "%% Begin Waypoint %%" OR "%% End Waypoint %%")')
        createConfigurationFileLayout.addWidget(self.createConfigurationFileInputFileInput)

        self.createConfigurationFileRunButton = QPushButton('Run', self)
        self.createConfigurationFileRunButton.clicked.connect(self.startCreatingConfigurationFile)
        createConfigurationFileLayout.addWidget(self.createConfigurationFileRunButton)

        self.createConfigurationFileLabel = QLabel('', self)
        createConfigurationFileLayout.addWidget(self.createConfigurationFileLabel)

        self.createConfigurationFileGroupbox.setLayout(createConfigurationFileLayout)
        
        
        self.createBranchGroupbox = QGroupBox("Create Branch", self)
        
        createBranchLayout = QVBoxLayout()

        self.createConfigurationFileInput = QLineEdit(self)
        self.createConfigurationFileInput.setPlaceholderText('Enter Configuration File Absolute Path')
        self.createConfigurationFileInput.setToolTip('(Add ".txt" Extension File)\n\n(To Create Branch)')
        createBranchLayout.addWidget(self.createConfigurationFileInput)

        self.createParentFolderInput = QLineEdit(self)
        self.createParentFolderInput.setPlaceholderText('Enter Parent Folder Absolute Path')
        self.createParentFolderInput.setToolTip('(Optional)\n\n(To Create Keywords Markdown Files)')
        createBranchLayout.addWidget(self.createParentFolderInput)
        
        self.createKeywordsInput = QLineEdit(self)
        self.createKeywordsInput.setPlaceholderText('Enable Keywords')
        self.createKeywordsInput.setToolTip('(Optional)\n\n(To Create Keywords Markdown Files)\n\n("Keywords" Folder In Parent Folder Required)\n\n(Enter "true" To Enable Keywords)\n\n(Empty By Default)')
        createBranchLayout.addWidget(self.createKeywordsInput)

        self.createBranchInput = QLineEdit(self)
        self.createBranchInput.setPlaceholderText('Enter Branch Absolute Path')
        self.createBranchInput.setToolTip('(Enter An Absolute Folder Path Where Arborescence Will Be Created)')
        createBranchLayout.addWidget(self.createBranchInput)

        self.createRunButton = QPushButton('Run', self)
        self.createRunButton.clicked.connect(self.startCreatingBranch)
        createBranchLayout.addWidget(self.createRunButton)

        self.createBranchLabel = QLabel('', self)
        createBranchLayout.addWidget(self.createBranchLabel)

        self.createBranchGroupbox.setLayout(createBranchLayout)

        
        self.configureParentFolderGroupbox = QGroupBox("Create Branch Internal Links", self)
        
        configureParentFolderLayout = QVBoxLayout()
        
        self.configureKeywordsFileInput = QLineEdit(self)        
        self.configureKeywordsFileInput.setPlaceholderText('Enter Keywords File Absolute Path')
        self.configureKeywordsFileInput.setToolTip('(Optional)\n\n(To Create Internal Links In "Keywords" Markdown File)\n\n("Keywords" Folder In Parent Folder Required)\n\n("Keywords" Markdown File In "Keywords" Folder Required)')
        configureParentFolderLayout.addWidget(self.configureKeywordsFileInput)
        
        self.configureBranchInput = QLineEdit(self)        
        self.configureBranchInput.setPlaceholderText('Enter Branch Absolute Path')
        self.configureBranchInput.setToolTip('(Enter An Absolute Folder Path Where Arborescence Will Be Created)')
        configureParentFolderLayout.addWidget(self.configureBranchInput)
        
        self.configureParentFolderConfirmLocationButton = QPushButton('Confirm Location', self)
        self.configureParentFolderConfirmLocationButton.clicked.connect(self.showDialog)
        configureParentFolderLayout.addWidget(self.configureParentFolderConfirmLocationButton)
        
        self.configureParentFolderStartButton = QPushButton('Start', self)
        self.configureParentFolderStartButton.clicked.connect(self.startProcessing)
        configureParentFolderLayout.addWidget(self.configureParentFolderStartButton)

        self.configureParentFolderStopButton = QPushButton('Interrupt', self)
        self.configureParentFolderStopButton.clicked.connect(self.stopProcessing)
        configureParentFolderLayout.addWidget(self.configureParentFolderStopButton)
        
        self.configureParentFolderLabel = QLabel('', self)
        configureParentFolderLayout.addWidget(self.configureParentFolderLabel)
        
        
        self.createBranchInternalLinksGroupbox = QGroupBox("Branch Internal Links Processing")
        
        createBranchInternalLinksLayout = QVBoxLayout()

        self.createBranchInternalLinksProgressBar = QProgressBar(self)
        self.createBranchInternalLinksProgressBar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        createBranchInternalLinksLayout.addWidget(self.createBranchInternalLinksProgressBar)

        self.createBranchInternalLinksGroupbox.setLayout(createBranchInternalLinksLayout)


        self.renameGroupbox = QGroupBox("Rename Branch Files And Branch Folders", self)
        
        renameLayout = QVBoxLayout()

        self.renameSearchingWordInput = QLineEdit(self)
        self.renameSearchingWordInput.setPlaceholderText('Enter Title')
        self.renameSearchingWordInput.setToolTip('(Optional)\n\n(Word To Search In All Branch File Names And Branch Folder Names)')
        renameLayout.addWidget(self.renameSearchingWordInput)

        self.renameReplacingWordInput = QLineEdit(self)
        self.renameReplacingWordInput.setPlaceholderText('Enter New Title')
        self.renameReplacingWordInput.setToolTip('(Optional)\n\n(Word To Replace In Branch File Names And Branch Folder Names)')
        renameLayout.addWidget(self.renameReplacingWordInput)

        self.renameProgressBar = QProgressBar(self)
        self.renameProgressBar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        renameLayout.addWidget(self.renameProgressBar)

        self.renameGroupbox.setLayout(renameLayout)
        
        
        self.refreshBranchInternalLinksGroupbox = QGroupBox("Refresh Branch Internal Links", self)
        
        refreshBranchInternalLinksLayout = QVBoxLayout()

        self.refreshBranchInternalLinksInput = QLineEdit(self)
        self.refreshBranchInternalLinksInput.setPlaceholderText('Empty By Default')
        self.refreshBranchInternalLinksInput.setToolTip('(Recommended If Branch Is Moved)\n\n(Enter "true" To Refresh Branch Internal Links)\n\n(Empty By Default)')
        refreshBranchInternalLinksLayout.addWidget(self.refreshBranchInternalLinksInput)

        self.refreshBranchInternalLinksProgressBar = QProgressBar(self)
        self.refreshBranchInternalLinksProgressBar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        refreshBranchInternalLinksLayout.addWidget(self.refreshBranchInternalLinksProgressBar)

        self.refreshBranchInternalLinksGroupbox.setLayout(refreshBranchInternalLinksLayout)
        
        
        configureParentFolderLayout.addWidget(self.createBranchInternalLinksGroupbox)
        configureParentFolderLayout.addWidget(self.renameGroupbox)
        configureParentFolderLayout.addWidget(self.refreshBranchInternalLinksGroupbox)
        
        self.configureParentFolderGroupbox.setLayout(configureParentFolderLayout)
        
        
        functionalitiesLayout.addWidget(self.createConfigurationFileGroupbox)
        functionalitiesLayout.addWidget(self.createBranchGroupbox)
        functionalitiesLayout.addWidget(self.configureParentFolderGroupbox)

        self.functionalitiesGroupbox.setLayout(functionalitiesLayout)
                
        self.functionalitiesScrollArea.setWidget(self.functionalitiesGroupbox)


        mainLayout.addWidget(self.functionalitiesScrollArea)


        self.setLayout(mainLayout)


        self.functionalities = None




    def showHelpDialog(self):
        
        
        helpDialogDialog = QDialog(self)
        helpDialogDialog.setWindowTitle("AppLPine 1.0 - Help")
        helpDialogDialog.setFixedWidth(int(QApplication.primaryScreen().availableGeometry().width() * 0.35))
        helpDialogDialog.setFixedHeight(int(QApplication.primaryScreen().availableGeometry().height() * 0.65))
        
        helpDialogLayout = QHBoxLayout(helpDialogDialog)
        
        helpDialogPixmap = QPixmap(os.getcwd() + "/Icon.png")
        
        helpDialogPixmapLabel = QLabel()
        helpDialogPixmapLabel.setPixmap(helpDialogPixmap.scaledToWidth(50, Qt.TransformationMode.SmoothTransformation))
        helpDialogPixmapLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        helpDialogLayout.addWidget(helpDialogPixmapLabel)
        
        
        informationScrollArea = QScrollArea()
        informationScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        informationScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        informationScrollArea.setWidgetResizable(True)
        
        informationGroupbox = QGroupBox()
        informationGroupbox.setStyleSheet("border: 1px solid rgb(89, 74, 53);")
        
        informationLayout = QVBoxLayout()
        
        
        inputFileScrollArea = QScrollArea()
        inputFileScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        inputFileScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        inputFileScrollArea.setWidgetResizable(True)
        
        inputFileGroupBox = QGroupBox()
        inputFileGroupBox.setStyleSheet("border: 1px solid rgb(89, 74, 53);")
        
        inputFileLayout = QVBoxLayout()
        
        inputFileLabel = QLabel()
        inputFileLabel.setText(
        """
        <html>
            <body>
                <pre>
                    \nHi! o/
                    \n
                    \nI created AppLPine as an open source organisational 
                    \ntool.
                    \n
                    \nThe aim of AppLPine is to contribute to the improvement
                    \nof daily information processing and access.
                    \n
                    \nKeep in mind that AppLPine can be WIDELY combined with
                    \nother applications, such as LibreOffice for editing
                    \nnumbered lists of notes, or Obsidian for navigating
                    \nthrough large data tree structures.
                    \n
                    \nI made this section as a memo, to provide you with
                    \nsome guidance regarding the way the app works.
                    \n
                    \nDon't hesitate to come back here if needed! :)
                    \n
                    \nBasically, the aim of AppLPine is to transform a 
                    \nnumbered list of daily notes into an arborescence 
                    \n(also known as tree structure) which is created 
                    \nin a specified folder in your computer.
                    \n
                    \nTo do so, the process involves several stages :
                    \n
                    \nThe first step is to select a numbered list of notes,
                    \nwhose contents do not countain any "&" characters,
                    \nexcept for titles where theirs levels and names must
                    \nbe separated by this character.
                    \nThis list must be exported in a popular file
                    \nformat, with PDF chosen here.
                    \n
                    \nKeep in mind that you can copy/paste a file or a
                    \nfolder directly into an input field to obtain
                    \nits absolute path.
                    \n
                    \nThen, you can try the functionalities by title, and
                    \nalso hover your mouse cursor over the input fields
                    \nto display the tooltips! :)
                    \n
                    \nThat said, hope you'll enjoy the app! &lt;3
                </pre>
            </body>
        </html>
        """)
        inputFileLayout.addWidget(inputFileLabel)
        
        inputFileGroupBox.setLayout(inputFileLayout)
        
        inputFileScrollArea.setWidget(inputFileGroupBox)
        
        
        fileGroupbox = QGroupBox()
        fileGroupbox.setStyleSheet("border: 1px solid rgb(89, 74, 53);")
        
        fileLayout = QVBoxLayout()
        
        fileLabel = QLabel("Here's a typical example of a notes file exported in PDF and processed by AppLPine :\n")
        fileLabel.setWordWrap(True)
        fileLayout.addWidget(fileLabel)
        
        
        fileContentScrollArea = QScrollArea()
        fileContentScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        fileContentScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        fileContentScrollArea.setWidgetResizable(True)
        
        fileContentGroupbox = QGroupBox()
        fileContentGroupbox.setStyleSheet("background-color: rgb(218, 192, 146); font-size: 10px; color: rgb(145, 121, 79);")
        
        fileContentLayout = QVBoxLayout()
        
        fileContentLabel = QLabel()
        fileContentLabel.setText(
        """
        \t1\t&\t<document name>
        \n
        \t\t1.1\t&\t<title>
        \n
        \t\t<content>
        \n
        \t\t\t1.1.1\t&\t<title>
        \t\t\t\t1.1.1.1\t&\t<title>
        \n
        \t\t\t\t<content>
        \n
        \t\t\t1.1.2\t&\t<title>
        \n
        \t\t\t<content>
        \n
        \t\t\t\t1.1.2.1\t&\t<title>
        \t\t\t\t1.1.2.2\t&\t<title>
        \n
        \t\t\t\t<content>
        \n
        \t\t\t\t1.1.2.2.1\t&\t<title>
        \t\t\t\t1.1.2.3\t&\t<title>
        \t\t\t\t1.1.2.4\t&\tKeywords [<word group>, ... , <word group> ]
        \t\t\t1.1.3\t&\t<title>
        \t\t\t\t1.1.3.1\t&\t<title>
        \n
        \t\t\t\t<content>
        \n
        \t\t\t1.1.4\t&\tKeywords [<word group>, ... , <word group> ]
        \t\t1.2\t&\t<title>
        \n
        \t\t<content>
        \n
        \t\t\t1.2.1\t&\t<title>
        \n
        \t\t\t<content>
        """)
        fileContentLayout.addWidget(fileContentLabel)
        
        fileContentGroupbox.setLayout(fileContentLayout)
        
        fileContentScrollArea.setWidget(fileContentGroupbox)
        
        
        fileLayout.addWidget(fileContentScrollArea)

        fileGroupbox.setLayout(fileLayout)


        informationLayout.addWidget(inputFileScrollArea)
        informationLayout.addWidget(fileGroupbox)
        
        informationGroupbox.setLayout(informationLayout)
        
        informationScrollArea.setWidget(informationGroupbox)
        
        
        helpDialogLayout.addWidget(informationScrollArea)
        
        helpDialogDialog.exec()




    def showAboutDialog(self):
        
        
        aboutDialogDialog = QDialog(self)
        aboutDialogDialog.setWindowTitle("AppLPine 1.0 - About")
        aboutDialogDialog.setFixedWidth(int(QApplication.primaryScreen().availableGeometry().width() * 0.35))
        aboutDialogDialog.setFixedHeight(int(QApplication.primaryScreen().availableGeometry().height() * 0.65))
        
        aboutDialogLayout = QHBoxLayout(aboutDialogDialog)
        
        aboutDialogPixmap = QPixmap(os.getcwd() + "/Icon.png")
        
        aboutDialogPixmapLabel = QLabel()
        aboutDialogPixmapLabel.setPixmap(aboutDialogPixmap.scaledToWidth(50, Qt.TransformationMode.SmoothTransformation))
        aboutDialogPixmapLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        aboutDialogLayout.addWidget(aboutDialogPixmapLabel)
        
        
        aboutContentDialogScrollArea = QScrollArea()
        aboutContentDialogScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        aboutContentDialogScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        aboutContentDialogScrollArea.setWidgetResizable(True)
        
        aboutContentDialogLayout = QVBoxLayout()
        
        aboutContentDialogGroupbox = QGroupBox()
        aboutContentDialogGroupbox.setStyleSheet("border: 1px solid rgb(89, 74, 53);")
        
        aboutContentDialogLabel = QLabel()
        aboutContentDialogLabel.setText(
        """
        <html>
            <body>
                <pre>
                    \nThis application has been developed using Python and
                    \nPyQt6. It is an open source tool and is distributed under
                    \nGPL v3.0 licence (General Public License version 3.0).
                    \nConsequently, you are free to use, modify and redistribute
                    \nit in accordance with the terms of this license.
                    \nHowever, no guarantee is provided concerning its correct
                    \nuse.
                    \nYou use the application at your own risk.
                    \n
                    \nAppLPine is distributed on Linux in AppImage format,
                    \nand on Windows in executable format.
                    \n
                    \nTake care! &lt;3
                </pre>
            </body>
        </html>
        """)
        aboutContentDialogLabel.setOpenExternalLinks(True)
        aboutContentDialogLayout.addWidget(aboutContentDialogLabel)
        
        aboutContentDialogGroupbox.setLayout(aboutContentDialogLayout)
        
        aboutContentDialogScrollArea.setWidget(aboutContentDialogGroupbox)
        
        
        aboutDialogLayout.addWidget(aboutContentDialogScrollArea)
        
        aboutDialogDialog.exec()




    def showDialog(self):
        
        
        absolute_keywords_file_path = self.configureKeywordsFileInput.text().strip()
        absolute_branch_path = self.configureBranchInput.text().strip()
        
        if absolute_branch_path:
            
            self.configureParentFolderLabel.setText('Branch Selected.')
            self.selectedBranch = absolute_branch_path
            self.selectedKeywordsFile = absolute_keywords_file_path
        
        else:
            
            self.configureParentFolderLabel.setText('Incorrect Absolute Branch Path.')




    def startProcessing(self):
        
        
        if hasattr(self, 'selectedBranch'):
            
            absolute_keywords_file_path = ""
            
            if hasattr(self, 'selectedKeywordsFile'):
                
                absolute_keywords_file_path = self.selectedKeywordsFile
            
            searching_word = self.renameSearchingWordInput.text().strip()
            replacing_word = self.renameReplacingWordInput.text().strip()
            refresh_branch_internal_links_bool = self.refreshBranchInternalLinksInput.text().strip()
            
            self.functionalities = Functionalities(self.selectedBranch, absolute_keywords_file_path, searching_word, replacing_word, refresh_branch_internal_links_bool)
            
            self.functionalities.updateCreateBranchInternalLinksSignal.connect(self.updateCreateBranchInternalLinksProgressBar)
            self.functionalities.updateRenameBranchFilesFoldersSignal.connect(self.updateRenameProgressBar)
            self.functionalities.updateRefreshBranchInternalLinksSignal.connect(self.updateRefreshBranchInternalLinksProgressBar)
            
            self.functionalities.stopCreateBranchInternalLinksSignal.connect(self.stopCreateBranchInternalLinksProgressBar)
            self.functionalities.stopRenameBranchFilesFoldersSignal.connect(self.stopRenameProgressBar)
            self.functionalities.stopRefreshBranchInternalLinksSignal.connect(self.stopRefreshBranchInternalLinksProgressBar)
            
            self.functionalities.finished.connect(self.onFinished)
            
            self.functionalities.start()




    def updateCreateBranchInternalLinksProgressBar(self, value):
        
        
        self.createBranchInternalLinksProgressBar.setValue(value)
    
    
    
    
    def updateRenameProgressBar(self, value):
        
        
        self.renameProgressBar.setValue(value)
    
    
    
    
    def updateRefreshBranchInternalLinksProgressBar(self, value):
        
        
        self.refreshBranchInternalLinksProgressBar.setValue(value)




    def stopProcessing(self):
        
        
        if self.functionalities:
            
            self.functionalities.stop()
            self.configureParentFolderLabel.setText('Process Interrupted.')
            self.configureKeywordsFileInput.clear()
            self.configureBranchInput.clear()
            self.renameSearchingWordInput.clear()
            self.renameReplacingWordInput.clear()
            self.refreshBranchInternalLinksInput.clear()




    def stopCreateBranchInternalLinksProgressBar(self):
        
        
        self.createBranchInternalLinksProgressBar.setValue(0)
    
    
    
    
    def stopRenameProgressBar(self):
        
        
        self.renameProgressBar.setValue(0)
    
    
    
    
    def stopRefreshBranchInternalLinksProgressBar(self):
        
        
        self.refreshBranchInternalLinksProgressBar.setValue(0)
    
    
    
    
    def onFinished(self):
        
        
        self.configureParentFolderLabel.setText('Process Finished.')
        self.configureKeywordsFileInput.clear()
        self.configureBranchInput.clear()
        self.renameSearchingWordInput.clear()
        self.renameReplacingWordInput.clear()
        self.refreshBranchInternalLinksInput.clear()
    
    
    
    
    def startCreatingConfigurationFile(self):
        
        
        self.createConfigurationFileLabel.clear()
        
        absolute_input_file_path = self.createConfigurationFileInputFileInput.text().strip()
        
        if absolute_input_file_path:
                
            Functionalities.create_configuration_file(absolute_input_file_path)
            
            self.createConfigurationFileLabel.setText('Configuration File Created.')
            
            self.createConfigurationFileInputFileInput.clear()
            
        else:
            
            self.createConfigurationFileLabel.setText('Incorrect Absolute Branch Path.')
    
    
    
    
    def startCreatingBranch(self):
        
        
        self.createBranchLabel.clear()
        
        absolute_configuration_file_path = self.createConfigurationFileInput.text().strip()
        absolute_parent_folder_path = self.createParentFolderInput.text().strip()
        absolute_branch_path = self.createBranchInput.text().strip()
        keywords_bool = self.createKeywordsInput.text().strip()
        
        if absolute_configuration_file_path and absolute_parent_folder_path and absolute_branch_path:
                
            Functionalities.create_branch(absolute_configuration_file_path, absolute_branch_path, absolute_parent_folder_path, keywords_bool)
                
            self.createBranchLabel.setText('Branch Created.')
            
            self.createConfigurationFileInput.clear()
            self.createParentFolderInput.clear()
            self.createBranchInput.clear()
            self.createKeywordsInput.clear()
            
        else:
            
            self.createBranchLabel.setText('Incorrect Input(s).')




# Main Program




if __name__ == '__main__':
    
    
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())

