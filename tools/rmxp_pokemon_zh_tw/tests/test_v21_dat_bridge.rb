# encoding: UTF-8
require 'tmpdir'
require 'csv'
root = File.expand_path('..', __dir__)
bridge = File.join(root, 'toolchain', 'essentials_v21_dat_bridge.rb')
Dir.mktmpdir do |d|
  default = Array.new(32); trans = Array.new(32)
  default[0] = []; default[0][1] = {'Hola {1}' => 'Hola {1}'}
  default[24] = {'Sí' => 'Sí'}
  trans[0] = []; trans[0][1] = {'Hola {1}' => 'Hello {1}'}
  trans[24] = {'Sí' => 'Yes', 'Borrar Partida' => 'Delete File'}
  File.binwrite(File.join(d,'default.dat'),Marshal.dump(default))
  File.binwrite(File.join(d,'english.dat'),Marshal.dump(trans))
  tsv=File.join(d,'m.tsv'); out=File.join(d,'zh.dat'); qa=File.join(d,'qa.tsv')
  raise unless system('ruby', bridge, 'export', File.join(d,'default.dat'), File.join(d,'english.dat'), tsv)
  rows=CSV.read(tsv,headers:true,col_sep:"\t",encoding:'bom|utf-8')
  raise "union failed" unless rows.length==3
  rows.each { |r| r['zh_tw']='你好 {1}' if r['translation']=='Hello {1}' }
  CSV.open(tsv,'wb',col_sep:"\t",write_headers:true,headers:rows.headers){|c| rows.each{|r| c<<r}}
  raise unless system('ruby', bridge, 'qa', tsv, qa, 'zh_tw')
  raise unless system('ruby', bridge, 'build', File.join(d,'english.dat'), tsv, out, 'zh_tw')
  built=Marshal.load(File.binread(out))
  raise unless built[0][1]['Hola {1}']=='你好 {1}'
end
puts 'PASS v21 dat bridge'
