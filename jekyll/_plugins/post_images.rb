# _plugins/post_images.rb
module Jekyll
  POST_IMAGES_DIR = '_posts/projects/images'
  DEST_IMAGES_DIR = 'projects/images'

  class PostImageFile < StaticFile
    def destination(dest)
      name_bits = @name.split('-', 4)
      date_dir = ''
      date_dir += "#{name_bits.shift}/" if name_bits.first.to_i > 0
      date_dir += "#{name_bits.shift}/" if name_bits.first.to_i > 0
      date_dir += "#{name_bits.shift}/" if name_bits.first.to_i > 0
      File.join(dest, date_dir + DEST_IMAGES_DIR, name_bits.join('-'))
    end
  end

  class PostImagesGenerator < Generator
    def generate(site)
      # Check for the images directory inside the posts directory.
      return unless File.exists?(POST_IMAGES_DIR)

      post_images = []

      # Process each image.
      Dir.foreach(POST_IMAGES_DIR) do |entry|
        if entry != '.' && entry != '..'
          site.static_files << PostImageFile.new(site, site.source, POST_IMAGES_DIR, entry)
          post_images << entry.gsub(File.extname(entry), '')
        end
      end

      # Remove images considered to be "actual" posts from the posts array.
      site.posts.each do |post|
        if post_images.include?(post.id[1..-1].gsub('/', '-'))
          site.posts.delete(post)
        end
      end
    end
  end
end
