module Jekyll
  class ProjectVersionTag < Liquid::Tag
    NO_GIT_MESSAGE = 'Oops, are you sure this is a git project?'
    UNABLE_TO_PARSE_MESSAGE = 'Sorry, could not read project version at the moment'

    def render(context)
      if git_repo?
        current_version.chomp
      else
        NO_GIT_MESSAGE
      end
    end

    private

    def current_version
      @_current_version ||= begin
        # attempt to find the latest tag, falling back to last commit
        version = git_describe || parse_head

        version || UNABLE_TO_PARSE_MESSAGE
      end
    end

    def git_describe
      tagged_version = %x{ git describe --tags --always }

      if command_succeeded?
        tagged_version
      end
    end

    def parse_head
      head_commitish = %x{ git rev-parse --short HEAD }

      if command_succeeded?
        head_commitish
      end
    end

    def command_succeeded?
      !$?.nil? && $?.success?
    end

    def git_repo?
      system('git rev-parse')
    end
  end
end

Liquid::Template.register_tag('project_version', Jekyll::ProjectVersionTag)
