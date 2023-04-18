from textual.app import App, ComposeResult
from textual.containers import Content, Vertical, Container
from textual.widgets import Header, Footer, Button, Input, Static, Label
from textual.widget import Widget
from textual.reactive import reactive
import os
import aiofiles
import asyncio
import subprocess

class SearchBar(Static):

    def filter_packages(self):
        filtered_list = [button for button in PackageList if self.search_term.lower() in button.lower()]
        return filtered_list


    def compose(self) -> ComposeResult:
        yield Button("Search", id="search", variant="default")
        yield Input(placeholder="Search...")

def GetPackages():
    output = subprocess.check_output(['brew', 'list'])
    return output.decode('utf-8').split('\n')


PackageList = GetPackages()


# def GetPackageInfo(PackageName):
#     output = PackageList
#     if PackageName == '':
#         PackageName = output[0]
#     PackageName = str(PackageName).lower()
#     piss = str(output[output.index("{}".format(PackageName))])
#     output = subprocess.check_output(['brew', 'info', piss])
#     return output

async def GetPackageInfo(package_name): #asking chatgpt AGAIN to help me with cache
    cache_directory = "cache"
    package_info_file = os.path.join(cache_directory, f"{package_name}.txt")
    if os.path.exists(package_info_file):
        with open(package_info_file, "r") as file:
            return file.read()


## normal code if no cache. 
    output = PackageList
    if package_name == '':
        package_name = output[0]
    package_name = str(package_name).lower()
    package_info = str(output[output.index("{}".format(package_name))])
    proc = await asyncio.create_subprocess_exec( # asked chatgpt for help with asyncio.
        'brew',
        'info',
        package_info,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()
    
    if stderr:
        return stderr.decode('utf-8')
    else:
        return stdout.decode('utf-8')

async def cache_package_info(package_name, filename):
    if not os.path.exists("cache"):
        os.mkdir("cache")

    package_info = await GetPackageInfo(package_name)
    async with aiofiles.open(f'cache/{filename}', mode='w') as file:
        await file.write(package_info)

class ButtonList(Vertical): # caching package info asynchronously with CHATGPT!!!
    def __init__(self):
        super().__init__()
        self.buttons = [button for button in PackageList] # refactor to include buttons attribute instead of pulling from output. need filter later on.

    def update_button_list(self, filtered_list):
        self.buttons = [button for button in filtered_list]

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        package_name = event.button.label
        cached_filename = "{}.txt".format(package_name)

        try:
            async with aiofiles.open(cached_filename,mode='r') as file:
                package_info = await file.read()
        except FileNotFoundError:
            package_info = await GetPackageInfo(package_name)
            asyncio.create_task(cache_package_info(package_name, cached_filename))

        InfoBoxContent.update_output(InfoBoxContent, package_info)

    def compose(self) -> ComposeResult:
        for x in self.buttons:
            yield Button(x)

class InfoBoxContent(Widget):
    package_info = reactive("")
    def __init__(self):
        super().__init__()
        self.package_info = reactive(GetPackageInfo(''))
    
    def update_output(self, outside_package_info):
        self.package_info = outside_package_info

    def render(self):
        return str(self.package_info)

class InfoBox(Content):
    def compose(self) -> ComposeResult:
        yield InfoBoxContent()

class brewui(App):  # todo: cache package info asynchronously on load
    # css
    CSS_PATH = "main.css"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("q", "quit", "Quit")]

    def compose(self) -> ComposeResult: # compose to construct a UI # widgets -> generator
        yield Header()
        yield SearchBar()
        yield ButtonList()
        yield InfoBox()
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark
    
    def quit() -> None:
        exit


if __name__ == "__main__":
    app = brewui()
    app.run()
