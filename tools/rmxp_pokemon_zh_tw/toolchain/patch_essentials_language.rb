# encoding: UTF-8
require 'zlib'

abort 'usage: ruby patch_essentials_language.rb INPUT_Scripts.rxdata OUTPUT_Scripts.rxdata [fragment] [label]' unless (2..4).include?(ARGV.length)
input, output = ARGV[0], ARGV[1]
fragment = ARGV[2] || 'zh_tw'
label = ARGV[3] || 'Traditional Chinese'

scripts = Marshal.load(File.binread(input))
raise 'Unexpected Scripts.rxdata structure' unless scripts.is_a?(Array)

settings_idx = scripts.index { |e| e.is_a?(Array) && e[1].to_s == 'Settings' }
msg_idx      = scripts.index { |e| e.is_a?(Array) && e[1].to_s == 'MessageConfig' }
raise 'Settings script not found' unless settings_idx
raise 'MessageConfig script not found' unless msg_idx

# Patch Settings::LANGUAGES.
settings = Zlib::Inflate.inflate(scripts[settings_idx][2]).force_encoding('UTF-8')
unless settings.include?(%Q(["#{label}", "#{fragment}"]))
  pattern = /(LANGUAGES\s*=\s*\[\s*\n(?:.*\n)*?\s*\["English",\s*"english"\]\s*)(\n\s*\])/m
  unless settings.match?(pattern)
    raise 'Could not find expected LANGUAGES block with English entry'
  end
  settings.sub!(pattern) { "#{$1},\n    [\"#{label}\", \"#{fragment}\"]#{$2}" }
end
scripts[settings_idx][2] = Zlib::Deflate.deflate(settings)

# Patch MessageConfig to use a system-installed CJK font only for zh_tw.
msg = Zlib::Inflate.inflate(scripts[msg_idx][2]).force_encoding('UTF-8')
unless msg.include?('CJK_FONT_NAMES')
  anchor = "  NARROW_FONT_Y_OFFSET     = 8\n"
  raise 'MessageConfig font anchor not found' unless msg.include?(anchor)
  insert = <<~'CODE'
    CJK_FONT_NAMES          = [
      "Noto Sans CJK TC", "Noto Sans TC", "Microsoft JhengHei UI", "Microsoft JhengHei",
      "Microsoft YaHei UI", "Microsoft YaHei", "Arial Unicode MS", "Droid Sans Fallback"
    ]
  CODE
  msg.sub!(anchor, anchor + insert.lines.map { |l| '  ' + l }.join)
end

helper_anchor = "  def self.pbDefaultSystemFontName\n"
unless msg.include?('def self.pbTraditionalChineseLanguage?')
  raise 'MessageConfig method anchor not found' unless msg.include?(helper_anchor)
  helper = <<~'CODE'
    def self.pbTraditionalChineseLanguage?
      return false if !$PokemonSystem || !defined?(Settings::LANGUAGES)
      lang = Settings::LANGUAGES[$PokemonSystem.language] rescue nil
      return lang && lang[1] == "zh_tw"
    end

  CODE
  msg.sub!(helper_anchor, helper.lines.map { |l| '  ' + l }.join + helper_anchor)
end

msg.sub!(
  /  def self\.pbDefaultSystemFontName\n.*?  end\n/m,
  <<~'CODE'.lines.map { |l| '  ' + l }.join
  def self.pbDefaultSystemFontName
    return MessageConfig.pbTryFonts(CJK_FONT_NAMES, FONT_NAME) if pbTraditionalChineseLanguage?
    return MessageConfig.pbTryFonts(FONT_NAME)
  end
  CODE
)
msg.sub!(
  /  def self\.pbDefaultSmallFontName\n.*?  end\n/m,
  <<~'CODE'.lines.map { |l| '  ' + l }.join
  def self.pbDefaultSmallFontName
    return MessageConfig.pbTryFonts(CJK_FONT_NAMES, SMALL_FONT_NAME) if pbTraditionalChineseLanguage?
    return MessageConfig.pbTryFonts(SMALL_FONT_NAME)
  end
  CODE
)
msg.sub!(
  /  def self\.pbDefaultNarrowFontName\n.*?  end\n/m,
  <<~'CODE'.lines.map { |l| '  ' + l }.join
  def self.pbDefaultNarrowFontName
    return MessageConfig.pbTryFonts(CJK_FONT_NAMES, NARROW_FONT_NAME) if pbTraditionalChineseLanguage?
    return MessageConfig.pbTryFonts(NARROW_FONT_NAME)
  end
  CODE
)

# Avoid stale cached font after switching language at runtime.
msg.sub!(
  /  def self\.pbGetSystemFontName\n.*?  end\n/m,
  <<~'CODE'.lines.map { |l| '  ' + l }.join
  def self.pbGetSystemFontName
    desired = pbDefaultSystemFontName
    @@systemFont = desired if !@@systemFont || @@systemFont != desired
    return @@systemFont
  end
  CODE
)
msg.sub!(
  /  def self\.pbGetSmallFontName\n.*?  end\n/m,
  <<~'CODE'.lines.map { |l| '  ' + l }.join
  def self.pbGetSmallFontName
    desired = pbDefaultSmallFontName
    @@smallFont = desired if !@@smallFont || @@smallFont != desired
    return @@smallFont
  end
  CODE
)
msg.sub!(
  /  def self\.pbGetNarrowFontName\n.*?  end\n/m,
  <<~'CODE'.lines.map { |l| '  ' + l }.join
  def self.pbGetNarrowFontName
    desired = pbDefaultNarrowFontName
    @@narrowFont = desired if !@@narrowFont || @@narrowFont != desired
    return @@narrowFont
  end
  CODE
)

scripts[msg_idx][2] = Zlib::Deflate.deflate(msg)
File.binwrite(output, Marshal.dump(scripts))
puts "Patched language '#{label}' (#{fragment}) -> #{output}"
puts "Settings script index=#{settings_idx}, MessageConfig index=#{msg_idx}"
