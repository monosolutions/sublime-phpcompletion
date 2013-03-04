import sublime
import sublime_plugin
import re


completions = []
propStrs = ['->','::']
string = ''
params = []


class SublimePHPCompletion(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):

        return completions

    def on_modified(self,view):
        global params,completions

        # getting word
        region = view.sel()[0]
        word = view.word(region)
        string = view.substr(word).strip();

        # we need to look for class instance
        if string in propStrs:

            # reset
            params = []
            completions = []

            classes = sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START | sublime.CLASS_LINE_END
            instance = view.substr(view.expand_by_class(word.a-1,classes))
            instanceOf = ''

            # static instance
            if string == '::':

                instanceOf = instance

            else:

                # find
                for variable in view.find_by_selector('variable.other.php'):

                    # looking for place where variable is instanciated
                    if instance == view.substr(variable):

                        instanceOf = view.substr(view.word(view.find('new\s+([a-z0-9_]+)', variable.b, sublime.IGNORECASE).b))


                        if instanceOf:
                            break

            self.getDefinition(view,instanceOf)

            params = sorted(params, key=lambda k: k['name'].lower())

            for param in params:
                completions.append((param['name'],re.sub('\$','\\$',param['val'])))


            if completions:
                view.run_command('auto_complete', {
                'disable_auto_insert': True,
                'api_completions_only': True,
                'next_completion_if_showing': False,
                })




    def getDefinition(self,view,instanceOf):

        location = view.window().lookup_symbol_in_index(instanceOf)

        # parse file based on location
        if location:

            filename = location[0][0]

            f = open(filename, mode='r')
            fileContent = f.read()

            # remove all comments
            #fileContent

            # does class extend
            result = re.search('class\s+'+instanceOf+'\s+extends ([a-z0-9_]+)', fileContent, re.I);

            if result:

                # load definitions for extended class
                self.getDefinition(view,result.group(1))

            # finding start of class
            for result in re.finditer('class\s+'+instanceOf+'(\s+[^\{]*)?\{', fileContent, re.I):

                posStart=result.start()

            # parse the class
            cBrackets = 0
            # function position
            fPos = []

            rLeft = re.compile('\{|\}')
            for left in rLeft.finditer(fileContent,posStart):

                posEnd=left.end()

                if left.group() == '{':
                    cBrackets += 1
                if left.group() == '}':
                    cBrackets -= 1

                # we found end if cBrackets = 0
                if cBrackets == 0:
                    break

            # getting functions
            rFunc = re.compile('public\s+(static\s+)?function\s+(([a-z0-9_]+)\s*\([^\)]*\))', re.I)
            for func in rFunc.finditer(fileContent,posStart,posEnd):
                params.append({'type': 'method','name': func.group(3),'val': func.group(2)})
                fPos.append(func.start())

            # get all params before second {
            rParam = re.compile('public\s+(static\s+)?$([^;\s]*)', re.I)
            for param in rParam.finditer(fileContent,posStart,fPos[0]):
                params.append({'type': 'property','name': param.group(2),'val': param.group(2)})
