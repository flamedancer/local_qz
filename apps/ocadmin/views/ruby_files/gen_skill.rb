# encoding: utf-8
# generate leader skill cfg
# puts "hello world"

require 'erb'
$BaseDir=File.expand_path(".", File.dirname(__FILE__))

strOutFile = File.expand_path("config_skill_out.txt", $BaseDir)
argv_input_file = ARGV[0] || $BaseDir + "/config_skill.rb"
argv_output_file= ARGV[1] || strOutFile

class SafeExpress
  # attr_accessor :l
  attr_accessor :r
  def initialize()
    @l = 1
    @r = 1
  end

  def self.check_expression(_expression, _origin)
      ret = true
      exp = SafeExpress.new
    
      strException = ""
      begin
        d = exp.instance_eval(_expression)
      rescue SyntaxError => ex
        strException = ex.to_s
        ret = false
      rescue => ex
        strException = ex.to_s
        ret = false    
      end  
    
      unless ret
        str = ""
        str << "in expresion:[#{_origin}]\n"
        str << "exception: " + strException
        str << "\n"            
        puts str
        raise "invalid expression"
      end
      ret
  end
  def self.parseFactorExpression(_expression)      
       _expression = _expression.to_s
       origin = _expression.dup       
       _expression.gsub!(":level", "l")
       _expression.gsub!(":recover", "r")       
       check_expression(_expression, origin)
       _expression                     
  end
end

class OutHelper
  class << self
    def indent_string(_str, _tabIndent)
      str = ""
      _str.each_line do |_line|
        str << _tabIndent << _line
      end
      str
    end
  end
end


class Bead
  attr_reader :name, :value
  def initialize(_name, _value)
    @name = _name
    @value = _value
  end
  def to_s
    "bead #{@name}:#{@value}"
  end
end

class BeadConfig 
  class << self
    @@hashBead = {}    
    def addBead(_name, _value, *_arrAlias)
      _name = _name.to_s
      @@hashBead[_name] = Bead.new(_name,_value)
      _arrAlias = _arrAlias || []
      _arrAlias.each do |_alias|
        addAlias(_name, _alias)
      end
    end
    def addAlias(_name, _alias)
      _name = _name.to_s
      _alias = _alias.to_s
      raise "#{_name} not exist" unless @@hashBead.has_key?(_name)
      @@hashBead[_alias] = @@hashBead[_name]     
    end
    def getBead(_name_or_alias)
      _name_or_alias = _name_or_alias.to_s
      raise "#{_name_or_alias} not exist" unless @@hashBead.has_key?(_name_or_alias)
      @@hashBead[_name_or_alias] 
    end 
  end
end

class AttrConfig
  class << self
    def getAttr(_name_or_alias)
       BeadConfig.getBead(_name_or_alias)
    end
  end
end


class SkillConfig
  class << self
    @@types = {}
    def addType(_name, _value)
      add_config_type(:type, _name, _value)
    end
    def getType(_name)
      get_config_type(:type, _name)            
    end
    def checkType(_name)
      check_config_type(:type, _name)
    end
    
    @@aoes = {}
    def addAoe(_name, _value)
      add_config_type(:aoe, _name, _value)
    end
    def getAoe(_name)
      get_config_type(:aoe, _name)   
    end
    def checkAoe(_name)
      check_config_type(:aoe, _name)
    end
    
    @@buff_ids = {}
    def addBuffId(_name, _value)
      add_config_type(:buff_id, _name, _value)
    end
    def getBuffId(_name)
      get_config_type(:buff_id, _name) 
    end
    def checkBuffId(_name)
      check_config_type(:buff_id, _name)
    end  
    
    @@leader_skill_types = {}
    def addLeaderSkillType(_name, _value)
      add_config_type(:leader_skill, _name, _value)
    end
    def getLeaderSkillType(_name)
      get_config_type(:leader_skill, _name)            
    end
    def checkLeaderSkillType(_name)
      check_config_type(:leader_skill, _name)
    end
    
    @@buff_default = {}
    # defaultOption = {:cd => 1, :prob => 1, :effect=> 1, :beads => []}  
    def add_buff_default_option(_buff_name, _option)
       _buff_name = _buff_name.to_s
       checkBuffId(_buff_name)
       originDefault = @@buff_default[_buff_name] || {} 
       _option = _option || {}
       newDefault = originDefault.merge(_option)       
       @@buff_default[_buff_name] = newDefault
    end
    
    def get_buff_default_option(_buff_name)
      _buff_name = _buff_name.to_s
      checkBuffId(_buff_name)
      defaultOption = @@buff_default[_buff_name] || {} 
    end
        
    private
    def add_config_type(_category, _name, _value)
      _name = _name.to_s
      hashValue = getHash(_category)      
      hashValue[_name] = _value
    end
    def get_config_type(_category, _name)
      _name = _name.to_s
      hashValue = getHash(_category)
      raise "#{_name} not exist in #{_category}" unless hashValue.has_key?(_name)
      hashValue[_name]
    end
    def check_config_type(_category,_name)
      _name = _name.to_s
      hashValue = getHash(_category)
      raise "#{_name} not exist in #{_category}" unless hashValue.has_key?(_name)
    end
    def getHash(_category)
      ret = case _category.to_s
      when "type"
        @@types
      when "aoe"
        @@aoes
      when "buff_id"
        @@buff_ids
      when "leader_skill"        
        @@leader_skill_types
      else
        raise "invalid category #{_category}"
      end
    end
  end  
end
defaultOption = {:enemy => false, :type => :attack, :aoe=> :single, :factor => 1.0}

BeadConfig.addBead(:gold, 4, :jin)
BeadConfig.addBead(:wood, 3, :mu)
BeadConfig.addBead(:water, 2, :shui)
BeadConfig.addBead(:fire, 1, :huo)
BeadConfig.addBead(:earth, 5, :tu)

SkillConfig.addType(:none, 0)
SkillConfig.addType(:attack, 1)
SkillConfig.addType(:recover, 2)
SkillConfig.addType(:buff, 3)

SkillConfig.addAoe(:single, 1)
SkillConfig.addAoe(:all, 2)
SkillConfig.addAoe(:rand, 3)

SkillConfig.addBuffId(:defense_down, 1) #弱体(虚弱)
SkillConfig.addBuffId(:curse, 2) #诅咒（被封技）
SkillConfig.addBuffId(:recover_down, 3) #病气(患病)（疲劳）
SkillConfig.addBuffId(:cant_move, 4) #麻痹
SkillConfig.addBuffId(:poison, 5) #毒

SkillConfig.addBuffId(:attack_down, 6) #怪我(受伤)（无力）
SkillConfig.addBuffId(:critical_up, 7) #爆击率up
SkillConfig.addBuffId(:bc_drop_up, 8) #BC出现率up
SkillConfig.addBuffId(:hc_drop_up, 9) #HC出现率up
SkillConfig.addBuffId(:recover_up, 10) #回复力up

SkillConfig.addBuffId(:add_hp, 11) #每回合回血
SkillConfig.addBuffId(:defense_up, 12) #防御力up
SkillConfig.addBuffId(:attack_up, 13) #攻击力up
SkillConfig.addBuffId(:attr_attack_up, 14) #指定属性攻击力up
SkillConfig.addBuffId(:add_bb, 15) #每回合回BB

SkillConfig.addBuffId(:drug_power_up, 16) #攻击力up(强化药)
SkillConfig.addBuffId(:drug_hard, 17) #防御力up(硬化药)
SkillConfig.addBuffId(:stone_attack, 18) #攻击力up(X击石)
SkillConfig.addBuffId(:stone_defense, 19) #防御力up(X护石)
SkillConfig.addBuffId(:angel, 20) #天使之像(承受一次致命打击)


SkillConfig.addBuffId(:equip_attack_up, 21) #装备使攻击力提升
SkillConfig.addBuffId(:equip_defense_up, 22) #装备使防御力提升
SkillConfig.addBuffId(:equip_rcv_up, 23) #装备使恢复力提升
SkillConfig.addBuffId(:equip_critical_up, 24) #装备使暴击率提升
SkillConfig.addBuffId(:recover_hc_up, 25) #血晶的回复量提升


SkillConfig.addBuffId(:break_armor, 26) #无视敌将防御
SkillConfig.addBuffId(:add_hp_by_hurt, 27) #吸血
SkillConfig.addBuffId(:drug_strong_power_up, 28) #强攻击力up(强大力丸)
SkillConfig.addBuffId(:drug_strong_hard, 29) #强防御力up(强金刚丸)
SkillConfig.addBuffId(:drug_power_hard_attack, 30) #攻击力up(大力金刚丸)

SkillConfig.addBuffId(:drug_power_hard_defense, 31) #防御力up(大力金刚丸)
SkillConfig.addBuffId(:mp_down, 32) #MP值降低
SkillConfig.addBuffId(:bead_hurt_up, 33) #连接A属性珠 A属性的武将伤害提升
SkillConfig.addBuffId(:beadA_change_beadB, 34) #将所有A属性珠转成B属性珠
SkillConfig.addBuffId(:remove_all_beadA, 35) #消除当前所有A属性珠子

SkillConfig.addBuffId(:clean_neg_buff, 36) #清除所有负面buff

class BufferData
  attr_accessor :id,  :cd, :prob, :effect, :beads
  def initialize(_id, _option = {})
    @id = _id.to_s        
    defaultOption = {:cd => 1, :prob => 1, :effect=> 1, :beads => []}    
    defaultOption.merge!(SkillConfig.get_buff_default_option(_id))    
    _option = defaultOption.merge(_option)
    
    SkillConfig.checkBuffId(_id)
    @cd = _option[:cd]
    @prob = _option[:prob]
    @effect = SafeExpress.parseFactorExpression(_option[:effect])
    
    
    arrBead = _option[:beads] || []
    unless arrBead.is_a?(Array)       
      arr = []
      arr.push arrBead
      arrBead = arr
    end
            
    @beads = arrBead.map do |_beadname|
      BeadConfig.getBead(_beadname)
    end    
  end
        
  def to_s
    # "7:3:1.0:0.15:1_2"
    str = ""
    str << "#{SkillConfig.getBuffId(@id)}:#{@cd}:#{@prob}:#{@effect}"    
    strBead = ":"
    @beads.each do |_bead|
      strBead << "#{_bead.value}_"
    end
    strBead.chop!
    str << strBead
    str
  end  
end

=begin
arrBeads = [:huo, "huo", "shui", "water", :water, :shui,:fire, "fire"]
arrBeads.each do |_bead|
  bead = BeadConfig.getBead(_bead)
  puts bead  
end
arrType = [:attack, :receive, :buff]
arrType.each do |_type|
  puts SkillConfig.getType(_type)
end
arrAoes = [:single, :aoe, :rand]
arrAoes.each do |_type|
  puts SkillConfig.getAoe(_type)
end
=end


class SkillData   
  attr_reader :card, :enemy, :type, :aoe, :factor, :comment
  attr_reader :buffs
  def initialize(_card, _option = {})
    @clear_neg_buf = false
    defaultOption = {:enemy => false, :type => :attack, :aoe=> :single, :factor => 1.0}
    @card = _card
    _option = defaultOption.merge(_option)
    @enemy = (_option[:enemy] == true)
    @type = _option[:type]
    SkillConfig.checkType(@type)
    @aoe = _option[:aoe]
    SkillConfig.checkAoe(@aoe)    
    @factor = SafeExpress.parseFactorExpression(_option[:factor])
    @comment = _option[:comment] || ""
    
    @clear_neg_buf = _option[:clear_neg_buf] || false
    @buffs = []
    
    
  end  
  
  def addClearNegBuf?
    bRet = false
    if @type.to_s == "recover"
      if @clear_neg_buf
        bRet = true
      end
    end
    bRet
  end
  
  def enemy?
    @enemy
  end
  
  def addBuff(_buff)
    @buffs.push _buff
  end
  
  def to_s
     # "1,         2,  0.0+(l-1)*0.02 [,buffer]* “
     str = ""
     return str if @type.to_s == "none"
     
     str << "#{SkillConfig.getType(@type)},#{SkillConfig.getAoe(@aoe)},#{@factor}"
     @buffs.each do |_buff|
       str << ", " << _buff.to_s
     end
     str
  end
  
  def to_comment
    # "1,         2,  0.0+(l-1)*0.02 | 1,2,0.2",                # 1  对敌将全体造成火属性4连伤害
    
    ret = ""
    unless @comment.empty?
      str = "主将技能:"
      str = "敌将技能:" if enemy?
      ret = "#{str}#{@comment}"
    end
    
    ret
  end
  
  private
    
end

class Skill
  attr_reader :card, :skilldata, :enemy_skilldata
  
  @@strDummy = ""
  class << @@strDummy
    def to_comment
      ""
    end
  end
  
  def initialize(_card)
    @card = _card.to_s    
    @skilldata = @@strDummy
    @enemy_skilldata = @@strDummy
  end
  def addSkillData(_skillData)    
       if _skillData.enemy?
         # puts "enemy==" + _skillData.to_s
         @enemy_skilldata = _skillData
       else
         @skilldata = _skillData
       end
  end
  
  def comment    
    strComment = @skilldata.to_comment
    enemyComment = @enemy_skilldata.to_comment
    str  = ""
    unless strComment.empty?
      str << "," << strComment
    end
    unless enemyComment.empty?
      str << "," << enemyComment
    end    
    "\#card_#{@card}#{str}"
  end
    
  def to_s
    strSkill = @skilldata.to_s
    strEnemySkill = @enemy_skilldata.to_s
    if strSkill.empty? and strEnemySkill.empty?
      return "\"\", #{comment}"       
    end
    "\"#{@skilldata}|#{@enemy_skilldata}\",    #{comment}"    
  end
end


SkillConfig.addLeaderSkillType(:incre_attack_with_attr, 1) #按照属性攻击力提升
SkillConfig.addLeaderSkillType(:decre_hurt_with_attr, 2)   #减伤
SkillConfig.addLeaderSkillType(:incre_mp,  3) #BB槽上升
SkillConfig.addLeaderSkillType(:incre_heart, 4) #HC回复提升 //心
SkillConfig.addLeaderSkillType(:spark_incre_attack, 5) #spark時、对敌方攻击值提升

SkillConfig.addLeaderSkillType(:spark_incre_bc_prob, 6) #spark時、BC出现率提升
SkillConfig.addLeaderSkillType(:spark_incre_gold_prob, 7)   #spark時、钱出現率提升
SkillConfig.addLeaderSkillType(:spark_incre_heart_prob,  8) #spark時、HC出現率提升
SkillConfig.addLeaderSkillType(:spark_incre_stone_prob, 9) #spark時、魂出現率提升
SkillConfig.addLeaderSkillType(:incre_mp_eor, 10) #回合结束时BB槽值增加. EOR(end of round)

SkillConfig.addLeaderSkillType(:incre_attack, 11) #全体攻击力提升
SkillConfig.addLeaderSkillType(:clear_all_exceptions, 12)   #所有异常状态无效
SkillConfig.addLeaderSkillType(:decre_hurt_with_all_attr,  13) #减小全体武将受到的伤害
SkillConfig.addLeaderSkillType(:incre_attack_has_five_attr, 14) #5种属性以上,攻击力提升
SkillConfig.addLeaderSkillType(:incre_defense_with_attr, 15) #按照属性防御力提升 //小数


SkillConfig.addLeaderSkillType(:critical_incre_hurt, 16) #暴击时伤害提升
SkillConfig.addLeaderSkillType(:prob_exception, 17)   #攻击时一定概率造成随机异常状态
SkillConfig.addLeaderSkillType(:prob_decre_hurt,  18) #低概率减少所受伤害
SkillConfig.addLeaderSkillType(:incre_mp_after_attack, 19) #受到攻击战意提升
SkillConfig.addLeaderSkillType(:prop_break_armor, 20) #低概率无视对方防御


SkillConfig.addLeaderSkillType(:prop_decre_hurt, 21) #低概率免疫所受伤害
SkillConfig.addLeaderSkillType(:incre_anger_groove_countdown, 22)   #怒气槽倒计时增加x秒
SkillConfig.addLeaderSkillType(:decre_anger_up_limit,  23) #怒气值上限减少x

class LeaderSkillItem
  attr_reader :card, :type, :effect, :prob, :attrs, :comment
  def initialize(_card, _option)
    defaultOption = {:type => :incre_attack_with_attr, :prob => 10.0}
    @card = _card    
    _option = defaultOption.merge(_option)
    
    @type = _option[:type]
    SkillConfig.checkLeaderSkillType(@type)
    @effect = SafeExpress.parseFactorExpression(_option[:effect])
    @prob = _option[:prob]
    
    @attrs = []
        
    attr = _option[:attrs] || []
        
    @comment = _option[:comment] || ""
    
    
    arrAttr = _option[:attrs] || []
    unless arrAttr.is_a?(Array)       
      arr = []
      arr.push arrAttr
      arrAttr = arr
    end
    @attrs = arrAttr.map do |_attr|
      AttrConfig.getAttr(_attr)
    end                    
  end 
  
  def has_comment?
    return false if comment.nil?
    bRet = comment.empty?
    return !bRet
  end
    
  def to_s
      # leaderSkillType, effect | prob, [attr,]*
      # "7,3|0.5,1.0:0.15:1_2"
      str = ""
      str << "#{SkillConfig.getLeaderSkillType(@type)},#{@effect}"    
      if @prob <= 2.0 
        str << "|#{@prob}"
      end
                  
      strAttr = ","
      @attrs.each do |_attr|
        strAttr << "#{_attr.value},"
      end
            
      strAttr.chop!
      str << strAttr
      str    
  end
end

class LeaderSkill
  attr_reader :card
  def initialize(_card)
    @card = _card    
    @arrSkills = []
  end
  
  def addSkillItem(_skillItem)
    @arrSkills.push _skillItem
    raise "leader skill just support at most two skills" if @arrSkills.size > 2
  end
          
  def to_s
    str = "\""
    strComment = "#card#{@card},"
    @arrSkills.each do |_item|
      str << _item.to_s << ":"
      strComment << _item.comment << "," if _item.has_comment?
    end
    strComment.chop!
    str.chop!
    str << "\",  "
    str << strComment
    str         
  end  
end


class SkillManager
  attr_reader :skills
  attr_reader :leaderSkills
  attr_reader :cur_leader_skill 
  
  
  def initialize()
    @skills = {}
    @leaderSkills = {}
    @cur_skill = nil
    @cur_leader_skill = nil
    @const_setting = {}
  end
  def add_skill(_card, _skilldata)  
    _card = _card.to_s
    skill = @skills.fetch(_card, nil)
    # puts "-----#{_card}, #{skill}"
    if skill.nil?
      skill = Skill.new(_card)
      @skills[_card] = skill      
    end
    skill.addSkillData(_skilldata)
  end
  
  def add_leader_skill(_card, _leader_skill_item)
    _card = _card.to_s
    leaderSkill = @leaderSkills.fetch(_card, nil)
    if leaderSkill.nil?
      leaderSkill = LeaderSkill.new(_card)
      @leaderSkills[_card] = leaderSkill
    end        
    leaderSkill.addSkillItem(_leader_skill_item)
  end
  
  def add_const_setting(_name, _value)
    @const_setting[_name.to_s] = _value
  end
  def get_const_setting(_name)
    @const_setting[_name.to_s] || 0
  end
    
  def output_data(_erb_template, _filename)
    
    str = ""    
    str, maxKey = out_skills(@skills, 0)
    strLeaderSkill, = out_skills(@leaderSkills, maxKey)
    
    strSkill = str
    strLeaderSkill = strLeaderSkill
    # puts _erb_template
    
    
    outErb = ERB.new(_erb_template)
    strOut = outErb.result(binding)
    
    File.open(_filename, "w:utf-8:utf-8") do  |_file|
      _file.write(strOut)   
      # _file.write(strSkill)  
    end
    puts "out #{maxKey} cards to file #{_filename}"
  end
  def setCurrentSkillData(_skill)
    @cur_skill = _skill
  end
      
  def setCurrentLeaderSkillData(_leaderSkill)
    @cur_leader_skill = _leaderSkill
  end
  
  def addBuffToCurrentSkillData(_buff)
    raise "current skill data is null" if @cur_skill.nil?
    @cur_skill.addBuff(_buff)
  end
  
private
   def out_skills(_hashSkills, _maxKey)
     str = ""
     arrKey = _hashSkills.keys.map do |_key|    
       _key.to_i
     end
     arrKey.sort!
     maxKey = arrKey[-1]
     maxKey = maxKey.to_i   
     maxKey = _maxKey if maxKey < _maxKey      
            
     (1..maxKey).each do |_card|      
       skillInstance = _hashSkills.fetch(_card.to_s,"\"\", \#card_#{_card}")
       str << skillInstance.to_s
       str << "\n"
     end
     [str, maxKey]
   end
   
end

$skillMgr = SkillManager.new

def skill(_option)
  card = _option[:card]
  skillData = SkillData.new(card, _option)
  $skillMgr.add_skill(card, skillData)
  
  
  $skillMgr.setCurrentSkillData(skillData)  
  if skillData.addClearNegBuf?
     buff(:id => :clean_neg_buff)  
  end    
  if block_given?    
    yield
  end
  $skillMgr.setCurrentSkillData(nil)
  # puts "use card #{card}"
end

def buff(_option)
   bufid = _option[:id]
   
   arr = _option[:beads]
   if arr.nil?   
     arrBeads = []         
     beadOne = _option[:bead] || ""
     
     unless beadOne.empty?
       arrBeads.push beadOne
       (2...10).each do |_index|
         beadIndex = "bead#{_index}".to_sym
         # puts beadIndex.class
         bead = _option[beadIndex] || ""
         # puts bead
         break if bead.empty?
         arrBeads.push bead
       end
     end
     arr = arrBeads
   end
   _option[:beads] = arr     
   
   instance =  BufferData.new(bufid, _option)   
   $skillMgr.addBuffToCurrentSkillData(instance)
end

def buff_config(_option)
  buff_id = _option[:id]
  SkillConfig.checkBuffId(buff_id)
  _option.delete(:id)
  SkillConfig.add_buff_default_option(buff_id, _option)  
end

def leader_skill(_option)
  card = _option[:card]
  _option.delete(:card)
  leaderSkillData = LeaderSkillItem.new(card, _option)
  $skillMgr.add_leader_skill(card, leaderSkillData)  
  $skillMgr.setCurrentLeaderSkillData(leaderSkillData)  
  if block_given? 
    yield
  end
  $skillMgr.setCurrentLeaderSkillData(nil)
end

def append_skill(_option)
  raise "invalid call append_skill  out the range leader_skill " if $skillMgr.cur_leader_skill.nil?
  card = $skillMgr.cur_leader_skill.card
  leaderSkillData = LeaderSkillItem.new(card, _option)
  $skillMgr.add_leader_skill(card, leaderSkillData)    
end

def skill(_option)  
  
  card = _option[:card]
  skillData = SkillData.new(card, _option)
  $skillMgr.add_skill(card, skillData)  
  
  $skillMgr.setCurrentSkillData(skillData)  
  if skillData.addClearNegBuf?
     buff(:id => :clean_neg_buff)  
  end
      
  if block_given? 
    yield
  end
  $skillMgr.setCurrentSkillData(nil)
  # puts "use card #{card}"
end

def add_config(_name, _value)  
  $skillMgr.add_const_setting(_name, _value)
end

loadFileName = argv_input_file
load loadFileName


strErbTemplate = File.expand_path("out_skill_template.erb", $BaseDir)
strErb = ""
File.open(strErbTemplate,"r") do |_file|
  strErb = _file.read
end


$skillMgr.output_data(strErb, argv_output_file)



=begin

def skill_cfg(_option)
  
end
  
#  "1,         2,  0.0+(l-1)*0.02 [,buffer]* | 1,2,0.2", 
# buffer => "7:3:1.0:0.15:1_2"
# :level  => l
add_skill(:card => 183,
          :enemy => true
          :type => :attack,  # :attack | :receive | :buff
          :aoe => :single,   # :single | :all | :random
          :factor => 1.2  #  number | "0.0+(:level-1)*0.02" | "0.0+(l-1)*0.03" 
          ) do
                        
     add_buffer(:id => 123,
                :cd => 1,
                :prob => 0.2,
                :effect => 0.2, 
                :bead => :huo, # :gold | :mood | :water | :fire | :earth
                               # :jin  | :mu   | :shui  | :huo  | :tu
                :bead2=> :shui) 
end

skill(:card => 183,
          :enemy => true
          :type => :attack,  # :attack | :receive | :buff
          :aoe => :single,   # :single | :all | :random
          :factor => 1.2  #  number | "0.0+(:level-1)*0.02" | "0.0+(l-1)*0.03" 
          ) 
          
skill(:card => 183,
      :factor => "0.0+(:level - 1 )*0.02"  #  number | "0.0+(:level-1)*0.02" | "0.0+(l-1)*0.03" 
     )   
=end
