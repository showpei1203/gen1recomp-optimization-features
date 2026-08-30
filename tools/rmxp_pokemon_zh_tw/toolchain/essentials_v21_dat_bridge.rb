# encoding: UTF-8
require 'csv'
require 'digest/sha1'

SECTION_NAMES = [
  'EVENT_TEXTS','SPECIES_NAMES','SPECIES_CATEGORIES','POKEDEX_ENTRIES','SPECIES_FORM_NAMES',
  'MOVE_NAMES','MOVE_DESCRIPTIONS','ITEM_NAMES','ITEM_NAME_PLURALS','ITEM_DESCRIPTIONS',
  'ABILITY_NAMES','ABILITY_DESCRIPTIONS','TYPE_NAMES','TRAINER_TYPE_NAMES','TRAINER_NAMES',
  'FRONTIER_INTRO_SPEECHES','FRONTIER_END_SPEECHES_WIN','FRONTIER_END_SPEECHES_LOSE',
  'REGION_NAMES','REGION_LOCATION_NAMES','REGION_LOCATION_DESCRIPTIONS','MAP_NAMES','PHONE_MESSAGES',
  'TRAINER_SPEECHES_LOSE','SCRIPT_TEXTS','RIBBON_NAMES','RIBBON_DESCRIPTIONS','STORAGE_CREATOR_NAME',
  'ITEM_PORTION_NAMES','ITEM_PORTION_NAME_PLURALS','POKEMON_NICKNAMES','TRAINER_SPEECHES_LOSE_F'
].freeze

TOKEN_RE = /(\\[A-Za-z]+\[[^\]]*\]|\\(?:PN|PM|CN|POG|pog|[brnlmfgG])|%\{[^}]+\}|%\d*\$?[sdif]|\{(?:\d+|[A-Za-z_][A-Za-z0-9_]*)\}|\$\{[^}]+\})/


def load_dat(path)
  x = Marshal.load(File.binread(path))
  raise "Expected Array in #{path}, got #{x.class}" unless x.is_a?(Array)
  x
end

def normalize_key(v)
  v.nil? ? '' : v.to_s
end

def entry_id(section_id, map_id, key_type, key)
  Digest::SHA1.hexdigest([section_id, map_id, key_type, normalize_key(key)].join('|'))[0,16]
end

def translated_value(trans, section_id, map_id, key, index)
  sec = trans[section_id] rescue nil
  return nil if sec.nil?
  if section_id == 0
    return nil unless sec.is_a?(Array)
    map = sec[map_id] rescue nil
    return nil unless map
    return map[key] if map.is_a?(Hash)
    return map[index] if map.is_a?(Array)
  elsif sec.is_a?(Hash)
    return sec[key]
  elsif sec.is_a?(Array)
    return sec[index]
  end
  nil
end

def each_union_entry(default, trans)
  max_sections = [default.length, trans.length].max
  max_sections.times do |section_id|
    dsec = default[section_id] rescue nil
    tsec = trans[section_id] rescue nil

    if section_id == 0
      dsec = [] unless dsec.is_a?(Array)
      tsec = [] unless tsec.is_a?(Array)
      max_maps = [dsec.length, tsec.length].max
      max_maps.times do |map_id|
        dm = dsec[map_id] rescue nil
        tm = tsec[map_id] rescue nil
        if dm.is_a?(Hash) || tm.is_a?(Hash)
          dh = dm.is_a?(Hash) ? dm : {}
          th = tm.is_a?(Hash) ? tm : {}
          keys = dh.keys + th.keys.reject { |k| dh.key?(k) }
          keys.each do |key|
            source = dh.key?(key) ? dh[key] : key
            translation = th.key?(key) ? th[key] : source
            yield(section_id, map_id, 'hash', key, nil, source, translation, !dh.key?(key))
          end
        elsif dm.is_a?(Array) || tm.is_a?(Array)
          da = dm.is_a?(Array) ? dm : []
          ta = tm.is_a?(Array) ? tm : []
          [da.length, ta.length].max.times do |idx|
            source = da[idx]
            translation = ta[idx]
            next if source.nil? && translation.nil?
            source = translation if source.nil?
            translation = source if translation.nil?
            yield(section_id, map_id, 'array', idx, idx, source, translation, da[idx].nil?)
          end
        end
      end
    elsif dsec.is_a?(Hash) || tsec.is_a?(Hash)
      dh = dsec.is_a?(Hash) ? dsec : {}
      th = tsec.is_a?(Hash) ? tsec : {}
      keys = dh.keys + th.keys.reject { |k| dh.key?(k) }
      keys.each do |key|
        source = dh.key?(key) ? dh[key] : key
        translation = th.key?(key) ? th[key] : source
        yield(section_id, '', 'hash', key, nil, source, translation, !dh.key?(key))
      end
    elsif dsec.is_a?(Array) || tsec.is_a?(Array)
      da = dsec.is_a?(Array) ? dsec : []
      ta = tsec.is_a?(Array) ? tsec : []
      [da.length, ta.length].max.times do |idx|
        source = da[idx]
        translation = ta[idx]
        next if source.nil? && translation.nil?
        source = translation if source.nil?
        translation = source if translation.nil?
        yield(section_id, '', 'array', idx, idx, source, translation, da[idx].nil?)
      end
    end
  end
end

def export_tsv(default_path, translation_path, out_path)
  default = load_dat(default_path)
  trans   = load_dat(translation_path)
  rows = 0
  CSV.open(out_path, 'wb', col_sep: "\t", write_headers: true,
           headers: %w[entry_id section_id section_name map_id key_type key source translation zh_tw status note]) do |csv|
    each_union_entry(default, trans) do |section_id, map_id, key_type, key, index, source, tr, translation_only|
      csv << [
        entry_id(section_id, map_id, key_type, key), section_id, SECTION_NAMES[section_id] || "SECTION_#{section_id}",
        map_id, key_type, normalize_key(key), source.to_s, tr.to_s, '', '', (translation_only ? 'translation_only_key' : '')
      ]
      rows += 1
    end
  end
  puts "Exported #{rows} entries -> #{out_path}"
end

def parse_key(key_type, key)
  key_type == 'array' ? key.to_i : key
end

def set_translation!(target, section_id, map_id, key_type, key, value)
  section_id = section_id.to_i
  key = parse_key(key_type, key)
  if section_id == 0
    map_id = map_id.to_i
    target[section_id] ||= []
    target[section_id][map_id] ||= (key_type == 'hash' ? {} : [])
    if target[section_id][map_id].is_a?(Hash)
      target[section_id][map_id][key] = value
    else
      target[section_id][map_id][key.to_i] = value
    end
  else
    target[section_id] ||= (key_type == 'hash' ? {} : [])
    if target[section_id].is_a?(Hash)
      target[section_id][key] = value
    else
      target[section_id][key.to_i] = value
    end
  end
end

def build_dat(baseline_path, manifest_path, out_path, column='zh_tw')
  target = load_dat(baseline_path)
  changed = 0
  CSV.foreach(manifest_path, headers: true, col_sep: "\t", encoding: 'bom|utf-8') do |row|
    value = row[column]
    next if value.nil? || value.empty?
    set_translation!(target, row['section_id'], row['map_id'], row['key_type'], row['key'], value)
    changed += 1
  end
  File.binwrite(out_path, Marshal.dump(target))
  puts "Built #{out_path}; applied #{changed} values from column #{column}"
end

def token_list(s)
  s.to_s.scan(TOKEN_RE).flatten
end

def qa_tsv(manifest_path, report_path, column='zh_tw')
  issues = []
  checked = 0
  CSV.foreach(manifest_path, headers: true, col_sep: "\t", encoding: 'bom|utf-8') do |row|
    target = row[column]
    next if target.nil? || target.empty?
    checked += 1
    src = row['translation'].to_s
    if token_list(src) != token_list(target)
      issues << [row['entry_id'], 'PLACEHOLDER_MISMATCH', row['section_name'], row['map_id'], src, target]
    end
    issues << [row['entry_id'], 'DECODE_REPLACEMENT_CHAR', row['section_name'], row['map_id'], src, target] if target.include?("\uFFFD")
  end
  CSV.open(report_path, 'wb', col_sep: "\t", write_headers: true,
           headers: %w[entry_id issue section map_id source translation]) do |csv|
    issues.each { |i| csv << i }
  end
  puts "QA checked #{checked} translated entries; issues=#{issues.length}; report=#{report_path}"
  exit(issues.empty? ? 0 : 2)
end

def stats(default_path, translation_path)
  default = load_dat(default_path)
  trans = load_dat(translation_path)
  total = 0
  translated = 0
  spanishish = 0
  each_union_entry(default, trans) do |section_id, map_id, key_type, key, index, source, tr, translation_only|
    total += 1
    translated += 1 if tr.to_s != source.to_s
    spanishish += 1 if tr.to_s.match?(/[¿¡áéíóúñÁÉÍÓÚÑ]/)
  end
  puts "entries=#{total} translated_vs_default=#{translated} spanish_accent_values=#{spanishish}"
end

cmd = ARGV.shift
case cmd
when 'export'
  abort 'usage: export DEFAULT.dat TRANSLATION.dat OUT.tsv' unless ARGV.length == 3
  export_tsv(*ARGV)
when 'build'
  abort 'usage: build BASELINE.dat MANIFEST.tsv OUT.dat [COLUMN]' unless (3..4).include?(ARGV.length)
  build_dat(ARGV[0], ARGV[1], ARGV[2], ARGV[3] || 'zh_tw')
when 'qa'
  abort 'usage: qa MANIFEST.tsv REPORT.tsv [COLUMN]' unless (2..3).include?(ARGV.length)
  qa_tsv(ARGV[0], ARGV[1], ARGV[2] || 'zh_tw')
when 'stats'
  abort 'usage: stats DEFAULT.dat TRANSLATION.dat' unless ARGV.length == 2
  stats(*ARGV)
else
  abort "commands: export | build | qa | stats"
end
